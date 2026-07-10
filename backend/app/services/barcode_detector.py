"""Server-side barcode detection in captured images.

Uses pyzbar (zbar wrapper) to detect barcodes in ESP32-captured images.
If the system library is not available, gracefully degrades (no-op).
"""
from dataclasses import dataclass
import logging
from typing import Optional

logger = logging.getLogger("pantry-api.barcode_detector")

try:
    from PIL import Image
    from pyzbar.pyzbar import decode as pyzbar_decode
    HAVE_PYZBAR = True
except ImportError:
    HAVE_PYZBAR = False
    logger.info("pyzbar not available — barcode detection in images disabled")


@dataclass
class DetectedBarcode:
    data: str
    barcode_type: str  # EAN13, UPC_A, CODE128, QRCODE, etc.
    confidence: float  # 0.0-1.0 estimate
    rect: Optional[dict] = None  # bounding box: {x, y, w, h}


def detect_barcodes(image_path: str) -> list[DetectedBarcode]:
    """Detect barcodes in an image file.

    Returns a list of detected barcode entries.
    Returns empty list if pyzbar is not installed or no barcodes found.
    """
    if not HAVE_PYZBAR:
        return []

    try:
        img = Image.open(image_path)
        # Convert to grayscale single-channel if needed
        if img.mode != "L":
            img = img.convert("L")

        decoded = pyzbar_decode(img)
        results = []
        for obj in decoded:
            rect = obj.rect
            results.append(DetectedBarcode(
                data=obj.data.decode("utf-8", errors="replace"),
                barcode_type=obj.type,
                confidence=1.0 if len(decoded) == 1 else 0.8,
                rect={
                    "x": rect.left,
                    "y": rect.top,
                    "w": rect.width,
                    "h": rect.height,
                } if rect else None,
            ))
            logger.info("Barcode detected in image", extra={
                "barcode": results[-1].data,
                "type": obj.type,
            })
        return results
    except Exception as e:
        logger.warning("Barcode detection failed on image", extra={
            "path": image_path,
            "error": str(e),
        })
        return []
