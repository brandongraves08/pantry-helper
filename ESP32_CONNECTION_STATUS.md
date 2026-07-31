# 🔧 ESP32 Device Connection Status

**Date:** January 20, 2026, 02:57 UTC  
**Status:** ✅ Backend Ready | ❌ Device Not Yet Connected

---

## What's Ready

### ✅ Backend System
- PostgreSQL database: **Created and initialized**
- FastAPI API: **Running and healthy**
- Device registration: **Configured**
- Device ID: `pantry-cam-001`
- Device Token: `QyRNM2kDF8anvaemTJlddemFD5OMcWgErYFImZ7Jx38`

### ✅ Firmware
- Built successfully (996 KB binary)
- Configured with:
  - WiFi: `Mine!` / `welcomehome`
  - Device Token: Updated with new token
  - API Endpoint: `http://rhel-01.thelab.lan:8000/v1/ingest`

---

## What's Needed

### 📱 Physical ESP32 Connection

Your firmware **has been updated with the correct device token** but needs to be uploaded to the ESP32 physical hardware.

**Options:**

1. **USB Serial Connection (Recommended)**
   ```bash
   # Connect ESP32 via USB cable with serial adapter
   cd /home/brandon/projects/pantry-helper/firmware
   python3 -m platformio device list  # Find USB port
   python3 -m platformio run -e esp32-cam -t upload --upload-port /dev/ttyUSB0
   ```

2. **WiFi OTA Upload** (if already running old firmware with OTA)
   ```bash
   python3 -m platformio run -e esp32-cam -t upload --upload-port 192.168.x.x
   ```

---

## Expected Behavior After Upload

1. **ESP32 boots:**
   ```
   === ESP32 BOOT ===
   Starting WiFi...
   Waiting for WiFi...
   WiFi connected! IP: 192.168.x.x
   Starting OTA...
   Starting Telnet...
   ```

2. **Automatic capture on boot:**
   ```
   [CAPTURE] Triggered by: boot
   [CAPTURE] → WiFi connected!
   [CAPTURE] → RSSI: -45 dBm
   [CAPTURE] → Uploading image to backend...
   [CAPTURE] ✓ Upload successful!
   ```

3. **Device shows online:**
   ```bash
   curl http://rhel-01.thelab.lan:8000/v1/devices
   ```
   Response:
   ```json
   {
     "status": "active",
     "last_seen_at": "2026-01-20T02:57:45Z",
     "total_captures": 1,
     "battery_v": 3.85,
     "rssi": -45
   }
   ```

---

## Next Actions

### Option 1: Use USB Serial Adapter
```bash
# 1. Connect ESP32 via USB with serial adapter
# 2. Put into flash mode (GPIO0 → GND, press RESET)
# 3. Run:
cd /home/brandon/projects/pantry-helper/firmware
python3 -m platformio run -e esp32-cam -t upload

# 4. Monitor serial output:
python3 -m platformio device monitor

# 5. Verify device online:
curl http://rhel-01.thelab.lan:8000/v1/devices
```

### Option 2: Check Telnet After Upload
```bash
# Once ESP32 is running and connected to WiFi:
nc -zv rhel-01.thelab.lan 23  # Check if telnet port is open
# If open, you can telnet for debugging
```

---

## System Status Summary

| Component | Status |
|-----------|--------|
| API Backend | ✅ Running |
| PostgreSQL | ✅ Initialized |
| Device Registry | ✅ Ready |
| Device Token | ✅ Generated |
| Firmware Binary | ✅ Built |
| Firmware Uploaded | ❌ Pending USB Connection |
| Device Online | ❌ Waiting for Upload |

---

## Quick Commands

```bash
# Check device status
curl http://rhel-01.thelab.lan:8000/v1/devices

# View API docs
http://rhel-01.thelab.lan:8000/docs

# Check backend logs
docker compose logs backend -f

# Monitor uploads
docker compose logs backend | grep -i "ingest\|POST"
```

---

**Next Step:** Connect ESP32 via USB and upload the firmware binary.
