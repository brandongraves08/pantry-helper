# ESP32 Firmware Build Guide - Local Machine

Since the build tools aren't available in this environment, follow these steps on your **local computer**.

---

## 🔧 **Step 1: Install Tools (First Time Only)**

### On Windows:
```powershell
# Install Python first from python.org (3.9+)
# Then open PowerShell and run:

pip install platformio
```

### On macOS:
```bash
pip3 install platformio
# Or via Homebrew:
brew install platformio
```

### On Linux:
```bash
pip3 install platformio
```

---

## 📥 **Step 2: Clone/Copy Project**

Get the pantry-helper repository on your local machine:

```bash
git clone https://github.com/brandongraves08/pantry-helper.git
cd pantry-helper/firmware
```

---

## ⚙️ **Step 3: Configure Device Settings**

Edit `src/config/config.cpp` with your settings:

```cpp
Config::Settings Config::settings = {
    .ssid = "YOUR_WIFI_SSID",
    .password = "YOUR_WIFI_PASSWORD",
    .device_id = "pantry-cam-001",
    .api_endpoint = "https://your-server.com/v1/ingest",
    .api_token = "iXQfmlnd6n7qO--qFqxd0AX7syxJZHdduZHs1VH-XWI",
    .light_threshold = 100,
    .quiet_period_ms = 30000,
};
```

**For local testing**, use:
```cpp
.api_endpoint = "http://192.168.X.X:8000/v1/ingest",  // Your computer's IP
.api_token = "iXQfmlnd6n7qO--qFqxd0AX7syxJZHdduZHs1VH-XWI",
```

---

## 🏗️ **Step 4: Build Firmware**

```bash
cd firmware

# Build the firmware
pio run -e esp32-cam

# You should see:
# Compiling...
# Linking...
# Building...
# ✔ Firmware built successfully
```

The compiled binary will be at: `.pio/build/esp32-cam/firmware.bin`

---

## 🔌 **Step 5: PLUG IN YOUR ESP32**

**→→→ CONNECT YOUR ESP32-CAM TO YOUR COMPUTER VIA USB CABLE NOW ←←←**

Wait 2-3 seconds for the device to be recognized.

---

## ⚡ **Step 6: Flash Firmware to Device**

Once connected, run:

```bash
pio run -e esp32-cam -t upload

# You should see:
# Uploading...
# Writing at 0x...
# [==========] 100%
# Leaving...
# Hard resetting via RTS pin...
```

**This takes 30-60 seconds.**

---

## 📡 **Step 7: Monitor Serial Output**

After uploading, watch the device startup:

```bash
pio device monitor

# You should see:
# ╔════════════════════════════════════════════╗
# ║     PANTRY CAMERA SYSTEM STARTING          ║
# ║         Phase 4: Full Firmware             ║
# ╚════════════════════════════════════════════╝
#
# [SETUP] Loading configuration...
# [SETUP] Device ID: pantry-cam-001
# [SETUP] Initializing power management...
# [SETUP] Initializing sensors...
# [SETUP] Initializing camera...
# [SETUP] ✓ All systems initialized
```

Press `Ctrl+C` to exit monitor.

---

## ✅ **Step 8: Verify Device Works**

The device will now:
1. Enter deep sleep
2. Wait for door/light trigger
3. Wake up and capture image
4. Connect to WiFi
5. Upload to API endpoint
6. Return to sleep

---

## 🧪 **Test Upload**

Check if images are arriving at your backend:

```bash
# Get device info
curl http://your-backend:8000/v1/devices

# Get captures from device
curl http://your-backend:8000/v1/devices/pantry-cam-001/captures
```

---

## ⚠️ **Common Issues**

### "Device not found"
- Check USB cable (data cable, not power-only)
- Try different USB port
- Verify device shows in system device manager

### "Serial port locked"
- Close any other serial monitors
- Unplug/replug device

### "Upload failed"
- Hold BOOT button during upload
- Try: `pio run -e esp32-cam -t upload --verbose`

### "WiFi won't connect"
- Check SSID is 2.4GHz (not 5GHz)
- Verify password is correct
- Check API endpoint is reachable

### "Camera initialization failed"
- Check OV2640 module is properly connected
- Verify I2C pullup resistors
- Try recompiling: `pio run -e esp32-cam --target clean`

---

## 📋 **Quick Reference**

```bash
# Build firmware
pio run -e esp32-cam

# Upload to device (plug in first!)
pio run -e esp32-cam -t upload

# Monitor serial output
pio device monitor

# Clean build
pio run -e esp32-cam -t clean

# Full rebuild
pio run -e esp32-cam -t clean
pio run -e esp32-cam
pio run -e esp32-cam -t upload
```

---

## 📞 **Next Steps After Upload**

1. ✅ Device is flashed
2. ✅ Device enters deep sleep
3. ✅ Open pantry door or turn on light → Device wakes
4. ✅ Image captured and uploaded to API
5. ✅ Check dashboard at http://localhost:3000

---

## 🎯 **Your Next Actions**

1. Install PlatformIO on your local machine
2. Edit `firmware/src/config/config.cpp` with your WiFi credentials
3. Plug in ESP32-CAM via USB
4. Run `pio run -e esp32-cam -t upload`
5. Monitor output with `pio device monitor`
6. Trigger device (open door/turn on light)
7. Check uploads in API/Dashboard

**That's it!** Your pantry camera will be live. 🚀

