#!/bin/bash
# Pantry Camera Setup Script for Raspberry Pi Zero 2 W
set -e

echo "=== Pantry Camera Setup ==="
echo "Setting up Pi Zero 2 W as pantry camera..."

# Update system
echo "[1/6] Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-picamera2 \
    libcamera-dev \
    libcamera-apps \
    wireless-tools \
    i2c-tools \
    vim

# Create directory structure
echo "[3/6] Creating directory structure..."
mkdir -p ~/pantry-camera
mkdir -p ~/pantry-camera/images
mkdir -p ~/pantry-camera/logs

# Copy files
echo "[4/6] Installing capture script..."
cd ~/pantry-camera
python3 -m venv venv
source venv/bin/activate
pip install requests

# Copy from repository (assumes git clone or manual copy)
if [ -f "capture_and_upload.py" ]; then
    cp capture_and_upload.py ~/pantry-camera/
    cp pantry-capture.service ~/pantry-camera/
else
    echo "WARNING: capture_and_upload.py not found in current directory"
    echo "Please copy it manually to ~/pantry-camera/"
fi

# Install systemd service
echo "[5/6] Installing systemd service..."
if [ -f "pantry-capture.service" ]; then
    sudo cp pantry-capture.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable pantry-capture.service
    echo "Service installed. Start with:"
    echo "  sudo systemctl start pantry-capture"
else
    echo "WARNING: pantry-capture.service not found"
fi

# Configure camera
echo "[6/6] Configuring camera..."
sudo raspi-config nonint do_camera 0  # Enable camera interface
echo "Camera interface enabled (reboot required)"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit /etc/systemd/system/pantry-capture.service with your API URL and token"
echo "2. Set environment variables in the service file"
echo "3. Test: sudo systemctl start pantry-capture"
echo "4. Check status: sudo systemctl status pantry-capture"
echo "5. View logs: sudo journalctl -u pantry-capture -f"
echo ""
echo "Reboot recommended: sudo reboot"
