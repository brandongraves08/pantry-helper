#!/usr/bin/env python3
"""Pantry camera client for Raspberry Pi Zero 2 W
Captures images and uploads to Pantry Inventory API
"""
import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# Configuration
API_URL = os.getenv("PANTRY_API_URL", "http://192.168.1.100:8000/v1/ingest")
DEVICE_ID = os.getenv("PANTRY_DEVICE_ID", "pantry-cam-001")
DEVICE_TOKEN = os.getenv("PANTRY_DEVICE_TOKEN", "")
CAPTURE_INTERVAL = int(os.getenv("PANTRY_INTERVAL", "3600"))  # seconds
IMAGE_DIR = Path("/tmp/pantry-images")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_battery_voltage():
    """Get battery voltage from Pi GPIO or power module"""
    try:
        # Placeholder - implement based on your hardware
        # For Pi with INA219 or similar power monitor
        return 4.2
    except Exception as e:
        logger.warning(f"Battery reading failed: {e}")
        return 0.0


def get_wifi_rssi():
    """Get WiFi signal strength (dBm)"""
    try:
        import subprocess
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True
        )
        # Parse iwconfig output for signal level
        # Example: Signal level=-45 dBm
        return -45  # Placeholder
    except Exception as e:
        logger.warning(f"WiFi RSSI reading failed: {e}")
        return -100


def capture_image():
    """Capture image using libcamera or picamera2"""
    timestamp = datetime.utcnow().isoformat()
    image_path = IMAGE_DIR / f"capture_{timestamp}.jpg"
    
    try:
        # Try libcamera-still first (modern Pi OS)
        import subprocess
        result = subprocess.run([
            "libcamera-still",
            "-o", str(image_path),
            "--width", "1280",
            "--height", "720",
            "--encoding", "jpg",
            "-n",  # No preview
            "-t", "1000"  # 1 second delay
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"libcamera failed: {result.stderr}")
            return None
            
        logger.info(f"Image captured: {image_path}")
        return image_path
        
    except FileNotFoundError:
        logger.error("libcamera-still not found")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Capture timeout")
        return None


def upload_image(image_path):
    """Upload image to Pantry Inventory API"""
    if not DEVICE_TOKEN:
        logger.error("No DEVICE_TOKEN set")
        return False
    
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Auto-capture from Pi Zero 2 W",
        "trigger_source": "timer"
    }
    
    try:
        with open(image_path, "rb") as f:
            files = {
                "image": (image_path.name, f, "image/jpeg")
            }
            data = {
                "device_id": DEVICE_ID,
                "token": DEVICE_TOKEN,
                "timestamp": metadata["timestamp"],
                "trigger_type": "timer",
                "battery_v": get_battery_voltage(),
                "rssi": get_wifi_rssi(),
                "metadata": json.dumps(metadata)
            }
            
            response = requests.post(
                API_URL,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Upload successful: {result['capture_id']}")
                return True
            else:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        logger.error("Upload timeout")
        return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False


def main():
    """Main capture loop"""
    logger.info("Pantry Camera Client Starting")
    logger.info(f"Device: {DEVICE_ID}")
    logger.info(f"API: {API_URL}")
    logger.info(f"Interval: {CAPTURE_INTERVAL}s")
    
    # Ensure image directory exists
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if running interactively or as service
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single capture mode
        image_path = capture_image()
        if image_path:
            upload_image(image_path)
            image_path.unlink(missing_ok=True)
    else:
        # Continuous loop mode
        while True:
            logger.info("Starting capture cycle")
            image_path = capture_image()
            
            if image_path:
                try:
                    upload_image(image_path)
                finally:
                    # Cleanup
                    image_path.unlink(missing_ok=True)
            
            logger.info(f"Sleeping {CAPTURE_INTERVAL}s")
            time.sleep(CAPTURE_INTERVAL)


if __name__ == "__main__":
    main()
