#!/usr/bin/env python3
"""
Demo script for Pantry Inventory System
Tests the complete flow: image upload → vision analysis → inventory update
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEVICE_ID = "pantry-cam-001"
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "test-token")

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"API is running at {API_BASE_URL}")
            return True
        else:
            print_error(f"API returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {API_BASE_URL}")
        print_info("Make sure the backend is running: make backend-run")
        return False
    except Exception as e:
        print_error(f"Error checking API health: {e}")
        return False

def create_test_image():
    """Create a simple test image for demo purposes"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with pantry items drawn
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw simple pantry items
        items = [
            ("Peanut Butter", (100, 100)),
            ("Pasta Box", (300, 100)),
            ("Tomato Sauce", (500, 100)),
            ("Rice Bag", (100, 300)),
            ("Cereal Box", (300, 300)),
        ]
        
        for item, (x, y) in items:
            # Draw rectangle
            draw.rectangle([x, y, x+120, y+150], outline='black', width=2)
            # Draw text
            draw.text((x+10, y+60), item, fill='black')
        
        # Save to temp file
        test_image_path = "/tmp/pantry_test.jpg"
        img.save(test_image_path, "JPEG")
        print_success(f"Created test image at {test_image_path}")
        return test_image_path
        
    except ImportError:
        print_warning("Pillow not installed, using placeholder image")
        # Create a minimal JPEG if Pillow is not available
        test_image_path = "/tmp/pantry_test.jpg"
        # Create minimal JPEG header
        with open(test_image_path, "wb") as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
            f.write(b'\xFF\xD9')  # EOI marker
        return test_image_path

def upload_test_image():
    """Upload a test image to the API"""
    print_header("Testing Image Upload")
    
    # Create or use test image
    image_path = create_test_image()
    
    # Prepare upload data
    with open(image_path, 'rb') as f:
        files = {'image': ('test.jpg', f, 'image/jpeg')}
        data = {
            'device_id': DEVICE_ID,
            'token': DEVICE_TOKEN,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'trigger_type': 'manual',
            'battery_v': 4.2,
            'rssi': -45,
        }
        
        print_info(f"Uploading image from device {DEVICE_ID}...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/v1/ingest",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success("Image uploaded successfully!")
                print_info(f"Capture ID: {result['capture_id']}")
                print_info(f"Status: {result['status']}")
                print_info(f"Message: {result['message']}")
                return result['capture_id']
            else:
                print_error(f"Upload failed with status {response.status_code}")
                print_error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print_error(f"Error uploading image: {e}")
            return None

def check_capture_status(capture_id, max_wait=30):
    """Check the status of a capture"""
    print_header("Checking Processing Status")
    
    print_info(f"Waiting for capture {capture_id} to be processed...")
    print_info("(This may take a few seconds if using OpenAI Vision API)")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE_URL}/v1/captures/{capture_id}")
            if response.status_code == 200:
                capture = response.json()
                status = capture.get('status', 'unknown')
                
                if status == 'complete':
                    print_success("Processing complete!")
                    return capture
                elif status == 'failed':
                    print_error("Processing failed!")
                    print_error(f"Error: {capture.get('error_message', 'Unknown error')}")
                    return None
                else:
                    print(f"  Status: {status}... waiting", end='\r')
                    time.sleep(2)
            else:
                print_warning(f"Could not check status (HTTP {response.status_code})")
                time.sleep(2)
        except Exception as e:
            print_error(f"Error checking status: {e}")
            return None
    
    print_warning("\nTimeout waiting for processing")
    return None

def get_inventory():
    """Get current inventory state"""
    print_header("Current Inventory")
    
    try:
        response = requests.get(f"{API_BASE_URL}/v1/inventory")
        if response.status_code == 200:
            inventory = response.json()
            
            if not inventory:
                print_warning("No items in inventory yet")
                return
            
            print(f"\n{Colors.BOLD}{'Item':<30} {'Count':<10} {'Confidence':<12} {'Last Seen'}{Colors.END}")
            print("-" * 80)
            
            for item in inventory:
                name = item['canonical_name']
                count = item.get('count_estimate', 0)
                confidence = item.get('confidence', 0)
                last_seen = item.get('last_seen_at', 'Never')[:19] if item.get('last_seen_at') else 'Never'
                
                conf_str = f"{confidence:.1%}" if confidence else "N/A"
                print(f"{name:<30} {count:<10} {conf_str:<12} {last_seen}")
            
            print()
            print_success(f"Total items: {len(inventory)}")
            
        else:
            print_error(f"Could not get inventory (HTTP {response.status_code})")
            
    except Exception as e:
        print_error(f"Error getting inventory: {e}")

def run_demo():
    """Run the complete demo"""
    print_header("🥫 Pantry Inventory System - Demo")
    
    print_info("This demo will:")
    print("  1. Check API health")
    print("  2. Upload a test image")
    print("  3. Wait for vision processing")
    print("  4. Display inventory results")
    print()
    
    # Step 1: Check API
    if not check_api_health():
        return 1
    
    # Step 2: Upload image
    capture_id = upload_test_image()
    if not capture_id:
        return 1
    
    # Step 3: Wait for processing
    capture = check_capture_status(capture_id)
    
    # Step 4: Show inventory
    get_inventory()
    
    print_header("Demo Complete")
    
    if capture and capture.get('status') == 'complete':
        print_success("All systems operational!")
        print_info("Try the web UI at http://localhost:5173")
        return 0
    else:
        print_warning("Demo completed with warnings")
        print_info("Check the logs for more details")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_demo()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)
