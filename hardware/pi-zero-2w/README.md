# Pi Zero 2 W Pantry Camera

Pantry inventory camera client for Raspberry Pi Zero 2 W.

## Hardware Requirements

- Raspberry Pi Zero 2 W
- Raspberry Pi Camera Module (v2 or HQ)
- microSD card (16GB+)
- 5V power supply
- WiFi network access

## Setup

### 1. Install Raspberry Pi OS

Download and flash Raspberry Pi OS (64-bit) to microSD:
```bash
# Enable SSH and WiFi before first boot
touch boot/ssh
cp wpa_supplicant.conf boot/
```

### 2. Configure WiFi (Optional)

Create `wpa_supplicant.conf` in boot partition:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourWiFiSSID"
    psk="YourWiFiPassword"
}
```

### 3. Install Pantry Camera

SSH into Pi and run:
```bash
curl -sSL https://raw.githubusercontent.com/yourrepo/pantry-helper/main/hardware/pi-zero-2w/setup.sh | bash
```

Or manually:
```bash
cd ~
git clone https://github.com/yourrepo/pantry-helper.git
cd pantry-helper/hardware/pi-zero-2w
chmod +x setup.sh
sudo ./setup.sh
```

### 4. Configure Environment

Edit the service configuration:
```bash
sudo systemctl edit --full pantry-capture
```

Set your API URL and token:
```ini
[Service]
Environment="PANTRY_API_URL=http://192.168.1.100:8000/v1/ingest"
Environment="PANTRY_DEVICE_ID=pantry-cam-001"
Environment="PANTRY_DEVICE_TOKEN=your-token-here"
Environment="PANTRY_INTERVAL=3600"
```

### 5. Start Service

```bash
# Start the service
sudo systemctl start pantry-capture

# Check status
sudo systemctl status pantry-capture

# View logs
sudo journalctl -u pantry-capture -f

# Auto-start on boot
sudo systemctl enable pantry-capture
```

## Usage

### Manual Capture (for testing)
```bash
cd ~/pantry-camera
source venv/bin/activate
python capture_and_upload.py --once
```

### Continuous Capture
The service runs automatically. Captures every hour by default.

### Change Capture Interval
Edit the service and restart:
```bash
sudo systemctl edit --full pantry-capture
# Change PANTRY_INTERVAL value (in seconds)
sudo systemctl restart pantry-capture
```

## Troubleshooting

### Camera not detected
```bash
# Check camera connection
vcgencmd get_camera

# Enable camera interface
sudo raspi-config
# Interface Options -> Camera -> Enable
```

### Upload failures
```bash
# Test API connectivity
curl -s http://your-server:8000/health

# Check logs
sudo journalctl -u pantry-capture -n 50

# Verify token
grep PANTRY_DEVICE_TOKEN /etc/systemd/system/pantry-capture.service
```

### Low memory
```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## File Structure

```
~/pantry-camera/
├── capture_and_upload.py    # Main capture script
├── venv/                    # Python virtual environment
├── images/                  # Temporary storage
└── logs/                    # Log files
```

## API Endpoints

The client uploads to:
```
POST /v1/ingest
Headers: X-Device-ID, X-Device-Token (or use form data)
Form Data:
  - device_id: string
  - token: string
  - timestamp: ISO 8601
  - trigger_type: "timer" | "manual"
  - battery_v: float
  - rssi: int
  - image: JPEG file
  - metadata: JSON string
```

## Development

### Edit on Pi
```bash
cd ~/pantry-camera
vim capture_and_upload.py
sudo systemctl restart pantry-capture
```

### View real-time logs
```bash
sudo journalctl -u pantry-capture -f
```

## Security

- Store API token securely (use systemd environment variables)
- Use HTTPS for production (configurable in PANTRY_API_URL)
- Restrict API access to local network via firewall

## Power Optimization

For battery-powered operation:
- Reduce capture interval (7200s = 2 hours)
- Lower image resolution (640x480)
- Disable HDMI output: `/usr/bin/tvservice -o`
- Lower CPU freq: `sudo cpufreq-set -g powersave`

---

Last updated: 2026-02-12
