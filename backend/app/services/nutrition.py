"""Nutrition info lookup via Open Food Facts search API.

Searches by product name (instead of barcode) so users can look up
nutrition data for items in their inventory.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger("pantry-api.nutrition")

OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
TIMEOUT_SECONDS = 10


@dataclass
class NutritionInfo:
    """Normalized nutrition data from a product search."""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: dict = field(default_factory=dict)
    allergens: list = field(default_factory=list)
    ingredients_text: Optional[str] = None
    source: str = "openfoodfacts"
    found: bool = False


def search_by_name(query: str, limit: int = 5) -> list[NutritionInfo]:
    """Search Open Food Facts by product name.

    Returns a list of matching products with nutrition data.
    Empty list if no results or on error.
    """
    params = {
        "search_terms": query.strip(),
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": min(limit, 20),
        "page": 1,
    }

    headers = {
        "User-Agent": "PantryHelper/1.0 (pantry-inventory-system; brandon@thelab.lan)",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(
            OPENFOODFACTS_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        logger.warning("Open Food Facts search timeout", extra={"query": query})
        return []
    except requests.ConnectionError as e:
        logger.warning("Open Food Facts connection error", extra={"query": query, "error": str(e)})
        return []
    except requests.RequestException as e:
        logger.warning("Open Food Facts search error", extra={"query": query, "error": str(e)})
        return []

    products = data.get("products", [])
    if not products:
        return []

    results = []
    for product in products[:limit]:
        nutriments = product.get("nutriments") or {}
        allergens_tags = product.get("allergens_tags") or []

        info = NutritionInfo(
            product_name=product.get("product_name") or product.get("product_name_en"),
            brand=product.get("brands"),
            category=product.get("categories"),
            barcode=product.get("code"),
            serving_size=product.get("serving_size"),
            image_url=product.get("image_front_url") or product.get("image_url"),
            nutrition={
                "energy_kcal": nutriments.get("energy-kcal_100g"),
                "protein_g": nutriments.get("proteins_100g"),
                "carbs_g": nutriments.get("carbohydrates_100g"),
                "fat_g": nutriments.get("fat_100g"),
                "fiber_g": nutriments.get("fiber_100g"),
                "sodium_g": nutriments.get("sodium_100g"),
                "sugars_g": nutriments.get("sugars_100g"),
            },
            allergens=[
                tag.replace("en:", "").replace("-", "_")
                for tag in allergens_tags
            ],
            ingredients_text=product.get("ingredients_text"),
            found=True,
        )
        results.append(info)

    logger.info(
        "Nutrition search results",
        extra={"query": query, "count": len(results)},
    )
    return results
