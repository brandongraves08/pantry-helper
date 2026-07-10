"""Barcode product lookup service.

Uses Open Food Facts (free, open, no API key) to look up product info
from a barcode. Falls back gracefully on network errors or unknown codes.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger("pantry-api.barcode")

OPENFOODFACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
TIMEOUT_SECONDS = 10


@dataclass
class BarcodeProduct:
    """Normalized product data from a barcode lookup."""
    barcode: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    package_type: Optional[str] = None
    ingredients_text: Optional[str] = None
    serving_size: Optional[str] = None
    nutriscore: Optional[str] = None
    image_url: Optional[str] = None
    quantity: Optional[str] = None  # e.g. "500 g", "12 oz"
    nutrition: dict = field(default_factory=dict)
    allergens: list = field(default_factory=list)
    source: str = "openfoodfacts"
    found: bool = False


def lookup_barcode(barcode: str) -> BarcodeProduct:
    """Look up a barcode via Open Food Facts and return normalized product data."""
    result = BarcodeProduct(barcode=barcode)

    # Strip common prefixes if present (GTIN prefix)
    clean = barcode.strip()
    url = OPENFOODFACTS_URL.format(barcode=clean)

    headers = {
        "User-Agent": "PantryHelper/1.0 (pantry-inventory-system; brandon@thelab.lan)",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        # Open Food Facts returns 404 for unknown barcodes — that's not an error
        if resp.status_code == 404:
            logger.info("Barcode not found in Open Food Facts", extra={"barcode": clean})
            return result
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        logger.warning("Open Food Facts timeout", extra={"barcode": clean})
        return result
    except requests.ConnectionError as e:
        logger.warning("Open Food Facts connection error", extra={
            "barcode": clean, "error": str(e),
        })
        return result
    except requests.RequestException as e:
        logger.warning("Open Food Facts HTTP error", extra={
            "barcode": clean, "status_code": resp.status_code if hasattr(resp, "status_code") else "?",
            "error": str(e),
        })
        return result

    if data.get("status") != 1:
        logger.info("Barcode not found in Open Food Facts (status=0)", extra={"barcode": clean})
        return result

    product = data.get("product") or {}
    result.found = True
    result.product_name = product.get("product_name") or product.get("product_name_en")
    result.brand = product.get("brands")
    result.category = product.get("categories")
    result.package_type = _infer_package_type(product.get("packaging"))
    result.ingredients_text = product.get("ingredients_text")
    result.serving_size = product.get("serving_size")
    result.nutriscore = product.get("nutriscore_grade")
    result.image_url = product.get("image_front_url") or product.get("image_url")
    result.quantity = product.get("quantity")

    # Nutrition per 100g
    nutriments = product.get("nutriments") or {}
    result.nutrition = {
        "energy_kcal": nutriments.get("energy-kcal_100g"),
        "protein_g": nutriments.get("proteins_100g"),
        "carbs_g": nutriments.get("carbohydrates_100g"),
        "fat_g": nutriments.get("fat_100g"),
        "fiber_g": nutriments.get("fiber_100g"),
        "sodium_g": nutriments.get("sodium_100g"),
        "sugars_g": nutriments.get("sugars_100g"),
    }

    # Allergens
    allergens_tags = product.get("allergens_tags") or []
    result.allergens = [
        tag.replace("en:", "").replace("-", "_")
        for tag in allergens_tags
    ]

    logger.info("Barcode lookup succeeded", extra={
        "barcode": clean,
        "product": result.product_name,
    })
    return result


def _infer_package_type(packaging: Optional[str]) -> Optional[str]:
    """Map Open Food Facts packaging string to our package_type vocabulary."""
    if not packaging:
        return None
    packaging_lower = packaging.lower()
    mapping = {
        "can": "can",
        "tin": "can",
        "jar": "jar",
        "bottle": "bottle",
        "box": "box",
        "carton": "box",
        "cardboard": "box",
        "bag": "bag",
        "pouch": "bag",
        "plastic": "plastic",
        "film": "plastic",
        "wrap": "plastic",
        "tetra": "tetra_pak",
        "tube": "tube",
        "tray": "tray",
        "sachet": "sachet",
    }
    for keyword, package_type in mapping.items():
        if keyword in packaging_lower:
            return package_type
    return "other"
