#!/bin/bash
# Quick ESP32 setup and build script
# Run this on your LOCAL machine (not in Docker)

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           PANTRY ESP32 - BUILD & UPLOAD SCRIPT            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if PlatformIO is installed
if ! command -v pio &> /dev/null; then
    echo "❌ PlatformIO not installed!"
    echo ""
    echo "Install it with:"
    echo "  pip3 install platformio"
    echo ""
    exit 1
fi

echo "✅ PlatformIO found: $(pio --version)"
echo ""

# Navigate to firmware directory
cd "$(dirname "$0")/firmware"

echo "════════════════════════════════════════════════════════════"
echo "Step 1: Building firmware..."
echo "════════════════════════════════════════════════════════════"
echo ""

if pio run -e esp32-cam; then
    echo ""
    echo "✅ Build successful!"
else
    echo ""
    echo "❌ Build failed. Check errors above."
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Step 2: Ready to upload"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🔌 PLUG IN YOUR ESP32-CAM NOW (via USB cable)"
echo ""
echo "Waiting for device... (you have 30 seconds)"
echo ""

# Give user time to plug in
for i in {30..1}; do
    echo -ne "   Seconds remaining: $i\r"
    sleep 1
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Step 3: Uploading to device..."
echo "════════════════════════════════════════════════════════════"
echo ""

if pio run -e esp32-cam -t upload; then
    echo ""
    echo "✅ Upload successful!"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Step 4: Monitoring device output"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Watching device startup... (Press Ctrl+C to stop)"
    echo ""
    
    pio device monitor
else
    echo ""
    echo "❌ Upload failed. Check errors above."
    exit 1
fi

echo ""
echo "✅ All done!"
