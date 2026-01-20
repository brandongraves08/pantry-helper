# 📱 ESP32 Quick Connect Guide

## Current Status
- ✅ Backend API is running and healthy
- ❌ No devices registered yet (0 devices found)
- ⏳ Waiting for first ESP32 connection

---

## Step-by-Step: Connect Your ESP32

### Step 1: Register Your Device (Do This First!)

**Option A: Using curl (command line)**
```bash
curl -X POST http://rhel-01.thelab.lan:8000/v1/admin/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kitchen Pantry Camera",
    "device_id": "pantry-cam-001"
  }'
```

**Option B: Using the API docs (browser)**
1. Open: http://rhel-01.thelab.lan:8000/docs
2. Find the `/v1/admin/devices` POST endpoint
3. Click "Try it out"
4. Enter:
   ```json
   {
     "name": "Kitchen Pantry Camera",
     "device_id": "pantry-cam-001"
   }
   ```
5. Click "Execute"

**Expected Response:**
```json
{
  "id": "some-uuid",
  "name": "Kitchen Pantry Camera",
  "device_id": "pantry-cam-001",
  "token": "iXQfmlnd6n7qO--qFqxd0AX7syxJZHdduZHs1VH-XWI",  ← COPY THIS!
  "created_at": "2026-01-19T22:00:00Z"
}
```

**⚠️ IMPORTANT: Copy and save the `token` value! You'll need it in Step 2.**

---

### Step 2: Configure Firmware WiFi and Device Token

Edit the file: `firmware/src/config/config.cpp`

Find the `_init_defaults()` function and update these lines:

```cpp
void Config::_init_defaults() {
    // ⬇️ UPDATE THESE VALUES ⬇️
    strcpy(Config::settings.ssid, "YOUR_WIFI_SSID");              // Your WiFi network name
    strcpy(Config::settings.password, "YOUR_WIFI_PASSWORD");       // Your WiFi password
    strcpy(Config::settings.device_id, "pantry-cam-001");         // Same as registered above
    strcpy(Config::settings.api_endpoint, "http://rhel-01.thelab.lan:8000/v1/ingest");
    strcpy(Config::settings.api_token, "YOUR_TOKEN_FROM_STEP_1"); // Token from registration
    // ⬆️ UPDATE THESE VALUES ⬆️
    
    Config::settings.light_threshold = 100;
    Config::settings.quiet_period_ms = 30000;
}
```

**Example (with real values):**
```cpp
strcpy(Config::settings.ssid, "MyHomeWiFi");
strcpy(Config::settings.password, "MySecurePassword123");
strcpy(Config::settings.device_id, "pantry-cam-001");
strcpy(Config::settings.api_endpoint, "http://rhel-01.thelab.lan:8000/v1/ingest");
strcpy(Config::settings.api_token, "iXQfmlnd6n7qO--qFqxd0AX7syxJZHdduZHs1VH-XWI");
```

---

### Step 3: Build Firmware

```bash
cd /home/brandon/projects/pantry-helper/firmware
python3 -m platformio run -e esp32-cam
```

**Expected Output:**
```
...
Building .pio/build/esp32-cam/firmware.bin
RAM:   [====      ]  40.2% (used 131644 bytes from 327680 bytes)
Flash: [======    ]  59.1% (used 1022896 bytes from 1732592 bytes)
SUCCESS
```

---

### Step 4: Connect ESP32-CAM via USB

1. **Connect USB cable:**
   - ESP32-CAM to your computer via USB-to-Serial adapter
   - Or use built-in USB on ESP32-S3 boards

2. **Verify connection:**
   ```bash
   python3 -m platformio device list
   ```
   
   **Expected Output:**
   ```
   /dev/ttyUSB0
   ------------
   Hardware ID: USB VID:PID=1A86:7523
   Description: USB2.0-Serial
   ```

---

### Step 5: Upload Firmware to ESP32

**For ESP32-CAM (requires boot mode):**
```bash
# Put ESP32-CAM in flash mode:
# 1. Connect GPIO0 to GND
# 2. Press RESET button
# 3. Run upload command:

python3 -m platformio run -e esp32-cam -t upload
```

**Expected Output:**
```
Uploading .pio/build/esp32-cam/firmware.bin
Writing at 0x00010000... (100%)
Wrote 1022896 bytes (582743 compressed)
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
SUCCESS
```

**After upload:**
1. Disconnect GPIO0 from GND
2. Press RESET button
3. ESP32 will boot normally

---

### Step 6: Monitor Serial Output

```bash
python3 -m platformio device monitor
```

**Expected Output (successful connection):**
```
╔════════════════════════════════════════╗
║     PANTRY CAMERA SYSTEM STARTING      ║
║         Phase 4: Full Firmware         ║
╚════════════════════════════════════════╝

[SETUP] Device ID: pantry-cam-001
[SETUP] Battery: 3.85V (78.5%)
[WIFI] Connecting to MyHomeWiFi...
[WIFI] ✓ Connected! IP: 192.168.1.150
[WIFI] RSSI: -45 dBm

[EVENT] Door trigger detected!
[EVENT] ✓ Image captured: 45823 bytes
[EVENT] Uploading to http://rhel-01.thelab.lan:8000/v1/ingest
[EVENT] ✓ Upload successful!

[SLEEP] Entering deep sleep mode...
```

---

### Step 7: Verify Device is Online

**Check device status via API:**
```bash
curl http://rhel-01.thelab.lan:8000/v1/devices
```

**Expected Output:**
```json
{
  "items": [
    {
      "id": "some-uuid",
      "name": "Kitchen Pantry Camera",
      "device_id": "pantry-cam-001",
      "status": "active",                    ← Device is online!
      "last_seen_at": "2026-01-19T22:05:00Z",
      "battery_v": 3.85,
      "rssi": -45,
      "total_captures": 1
    }
  ],
  "total": 1
}
```

**Check via Web Dashboard:**
Open: http://rhel-01.thelab.lan:3000

You should see your device listed with:
- Green "Active" status
- Battery level
- WiFi signal strength
- Last seen timestamp

---

## Troubleshooting

### ❌ Device not appearing after upload

**Check 1: WiFi credentials**
```bash
# Monitor serial output for WiFi errors
python3 -m platformio device monitor

# Look for:
[ERROR] WiFi connection failed
[ERROR] Failed to connect to MyHomeWiFi
```
→ **Fix:** Double-check WiFi SSID and password in config.cpp

**Check 2: API endpoint accessible**
```bash
# From ESP32's network, test if API is reachable
ping rhel-01.thelab.lan

# Test API endpoint
curl http://rhel-01.thelab.lan:8000/health
```
→ **Fix:** Ensure rhel-01.thelab.lan is accessible on your WiFi network

**Check 3: Device token valid**
```bash
# Verify device is registered
curl http://rhel-01.thelab.lan:8000/v1/devices | python3 -m json.tool
```
→ **Fix:** Re-register device if needed (Step 1)

**Check 4: Backend logs**
```bash
# Watch for incoming requests
docker compose logs backend -f

# Look for authentication errors
docker compose logs backend | grep -i "401\|403\|auth"
```

---

### ❌ Upload fails (connection errors)

**Serial output shows:**
```
[ERROR] Upload failed - will retry next wakeup
[ERROR] HTTP error: -1 (connection failed)
```

**Common causes:**
1. **API endpoint wrong:** Check `api_endpoint` in config.cpp
2. **Network unreachable:** ESP32 and backend not on same network
3. **Firewall blocking:** Port 8000 may be blocked

**Test from ESP32's network:**
```bash
# From a device on same WiFi as ESP32
curl -v http://rhel-01.thelab.lan:8000/health
```

---

### ❌ Authentication errors

**Backend logs show:**
```
ERROR - Authentication failed for device pantry-cam-001
```

**Fix:**
1. Verify token in config.cpp matches registered token
2. Re-register device if token is lost
3. Rebuild and re-upload firmware

---

### ❌ Camera initialization failed

**Serial output shows:**
```
[ERROR] Failed to initialize camera
```

**Fixes:**
1. Check camera ribbon cable is firmly connected
2. Verify camera module is compatible (OV2640)
3. Try lower camera resolution in camera.cpp
4. Power cycle the ESP32

---

## Quick Reference

### Register Device
```bash
curl -X POST http://rhel-01.thelab.lan:8000/v1/admin/devices \
  -H "Content-Type: application/json" \
  -d '{"name":"Kitchen Pantry","device_id":"pantry-cam-001"}'
```

### Build Firmware
```bash
cd firmware && python3 -m platformio run -e esp32-cam
```

### Upload Firmware
```bash
python3 -m platformio run -e esp32-cam -t upload
```

### Monitor Serial
```bash
python3 -m platformio device monitor
```

### Check Device Status
```bash
curl http://rhel-01.thelab.lan:8000/v1/devices | python3 -m json.tool
```

### View Recent Captures
```bash
curl http://rhel-01.thelab.lan:8000/v1/inventory/history | python3 -m json.tool
```

---

## Next Steps After Connection

1. ✅ Device registered and online
2. ✅ First image captured and uploaded
3. ⏳ Monitor inventory updates at http://rhel-01.thelab.lan:3000
4. ⏳ Adjust camera position for best pantry view
5. ⏳ Test trigger reliability (door/light sensors)
6. ⏳ Monitor battery life and charging

---

**Need Help?**
- Check backend logs: `docker compose logs backend -f`
- Check worker logs: `docker compose logs celery_worker -f`
- View API docs: http://rhel-01.thelab.lan:8000/docs
