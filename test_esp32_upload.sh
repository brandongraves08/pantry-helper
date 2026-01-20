#!/bin/bash

# Manual ESP32 Test - Simulate device capture and upload

DEVICE_ID="pantry-cam-001"
DEVICE_TOKEN="QyRNM2kDF8anvaemTJlddemFD5OMcWgErYFImZ7Jx38"
API_ENDPOINT="http://localhost:8000/v1/ingest"

echo "🧪 Testing ESP32 Device Upload..."
echo "Device ID: $DEVICE_ID"
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Create a dummy JPEG image (minimal valid JPEG)
DUMMY_IMAGE=$(cat <<'EOF'
/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k=
EOF
)

# Create a test image file
echo "Creating test image..."
echo -n "$DUMMY_IMAGE" | base64 -d > /tmp/test_image.jpg
ls -lh /tmp/test_image.jpg

# Test 1: Direct POST to ingest endpoint
echo ""
echo "Test 1: Direct upload simulation..."
curl -v -X POST "$API_ENDPOINT" \
  -H "Authorization: Bearer $DEVICE_TOKEN" \
  -H "X-Device-ID: $DEVICE_ID" \
  -F "image=@/tmp/test_image.jpg" \
  -F "trigger_type=test" \
  -F "battery_v=3.85" \
  -F "rssi=-45" \
  2>&1 | head -50

echo ""
echo ""

# Test 2: Check device status
echo "Test 2: Check device status..."
curl -s http://localhost:8000/v1/devices | python3 -m json.tool | grep -A 5 "pantry-cam-001"

echo ""
echo "Test complete!"
