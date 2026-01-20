# ESP32-CAM Pantry Helper - AI Agent Instructions

## Project Overview
This is an **ESP32-CAM firmware** for a battery-powered pantry monitoring device. It captures images triggered by door/light sensors, uploads them to a backend API via WiFi, and uses deep sleep for power efficiency. Built with **PlatformIO + Arduino framework**.

## Architecture & Module Design

### Module Organization
Code follows a **namespace-based modular architecture** in `src/`:
- `camera/` - OV2640 camera initialization and JPEG capture
- `upload/` - Multipart/form-data HTTP POST with retry logic
- `power/` - Deep sleep management and wake reason detection
- `sensors/` - Door (GPIO33) and light (GPIO34) sensor debouncing
- `net/` - WiFi connection management with timeout handling
- `config/` - Device settings (SSID, API endpoint, device_id)
- `telnet/` - Remote debugging console on port 23
- `ota/` - Over-the-air firmware updates
- ~~`webserver/`~~ - **DISABLED** (library issues - file renamed to `.disabled`)

### Critical Data Flow
1. **Boot/Sensor Trigger** → Check wake reason (timer/GPIO/power-on)
2. **WiFi Connect** → Start remote services (OTA, Telnet) if connected
3. **Camera Capture** → JPEG from OV2640 (800x600, quality 12)
4. **Upload** → POST to `/v1/ingest` with device_id, timestamp, battery_v, RSSI, image
5. **Deep Sleep** → Wake on timer (30s default) or GPIO33 (door sensor)

## ESP32-CAM Specific Constraints

### UART Pin Conflicts
- **Serial (UART0)** on GPIO1/3 **CONFLICTS** with camera pins
- Use `Serial2` (UART2) on GPIO16/17 for debug output if needed
- Current code uses `Serial` for simplicity but may have timing issues

### Memory Management
- **PSRAM enabled** via `-DBOARD_HAS_PSRAM` build flag
- Use `huge_app.csv` partition scheme for firmware size
- Camera framebuffer requires PSRAM - always check `config.fb_count` in camera init
- Free heap should stay above 50KB during upload operations

### GPIO Pin Assignments
```cpp
// Camera pins: GPIO 0,5,18-27,32,34-36,39 (see camera.cpp for full mapping)
GPIO33 - Door sensor (INPUT_PULLUP, ext0 wakeup)
GPIO34 - Light sensor (ADC) + Battery monitor (shared)
```

## Development Workflows

### Build & Upload Commands
```bash
# Build firmware (from firmware/ directory)
pio run -e esp32-cam

# Upload via USB (COM3 on Windows)
pio run -t upload

# Upload via OTA (after first USB flash)
pio run -t upload --upload-port 192.168.0.45

# Monitor serial output
pio device monitor --port COM3
# OR for remote debugging: telnet 192.168.0.45
```

### Remote Debugging Pattern
- **Serial output** goes to both `Serial` (USB) and `Serial2` (UART2)
- **Telnet server** mirrors logs over WiFi on port 23
- Use `TelnetServer::println(msg)` to send logs to all outputs
- Test with: `telnet <ESP32_IP>` or PowerShell TCP client (see terminal history)

### Testing with Simplified Firmwares
- `test_wifi.cpp` - WiFi + OTA + Telnet only (no camera/sensors)
- `test_serial_only.cpp` - Basic serial output test
- **Pattern:** Copy to `src/main.cpp`, build, upload, test, restore from `main.cpp.bak`

## Code Conventions & Patterns

### Multi-Output Logging Pattern
```cpp
String msg = "[MODULE] Log message";
Serial.println(msg);
Serial2.println(msg);
TelnetServer::println(msg);
Serial.flush();  // Always flush after critical logs
Serial2.flush();
```

### HTTP Upload Retry Strategy
- **3 retries max** with 2-second exponential backoff
- 15s connect timeout, 20s read/write timeout
- Uses `WiFiClientSecure` with GlobalSign Root CA certificate
- Multipart boundary: `----PantryImageBoundary1234567890`

### Configuration Access Pattern
```cpp
// config/config.h exposes quick-access pointers:
Config::ssid          // char*
Config::password      // char*
Config::device_id     // char*
Config::api_endpoint  // char*
Config::api_token     // char* (for Authorization: Bearer header)
```

### Sensor Debouncing
- **Built-in debouncing** in `Sensors::check_door()` and `check_light()`
- 50ms debounce window per sensor
- 30s "quiet period" prevents rapid re-triggers
- NO separate `debounce()` function calls needed

## Common Issues & Solutions

### WebServer Library Disabled
**Issue:** ESPAsyncWebServer has linker conflicts  
**Solution:** `webserver.cpp` renamed to `.disabled`, all `WebServer::` calls commented out  
**Pattern:** Use `// #include "webserver/webserver.h"` and `//WebServer::add_log(msg)`

### Upload Failures
- Check `Config::api_endpoint` format (must start with `https://`)
- Verify backend is running and reachable
- Check certificate expiry if SSL errors occur
- Monitor heap: `ESP.getFreeHeap()` should be >50KB before upload

### Deep Sleep Not Working
- Ensure `WiFi.disconnect()` called before sleep
- Disable Bluetooth explicitly if enabled
- GPIO33 must be LOW to wake (reed switch closes on door open)

## Integration Points

### Backend API Contract
```http
POST /v1/ingest HTTP/1.1
Content-Type: multipart/form-data; boundary=----PantryImageBoundary1234567890
Authorization: Bearer <api_token>

Fields: device_id, captured_at (ISO8601), trigger_type, battery_v, rssi, image (JPEG binary)
Expected: 200 OK on success
```

### OTA Update Credentials
- Password: `pantry2026` (see `platformio.ini`)
- Port: 3232 (default Arduino OTA)
- Call `OTA::init()` after WiFi connects

## Key Files to Reference
- [PHASE_4_IMPLEMENTATION.md](PHASE_4_IMPLEMENTATION.md) - Complete feature specs and hardware wiring
- [platformio.ini](platformio.ini) - Build flags, dependencies, OTA password
- [src/main.cpp](src/main.cpp) - Main event loop and capture trigger handling
- [src/upload/upload.cpp](src/upload/upload.cpp) - HTTP multipart upload implementation

## When Making Changes
1. **Always preserve logging** - Use multi-output pattern for all new features
2. **Test WiFi first** - Use `test_wifi.cpp` to validate remote services before camera changes
3. **Check heap usage** - Add `ESP.getFreeHeap()` logs before/after memory-intensive operations
4. **Update PHASE_4_IMPLEMENTATION.md** - Document new features with line counts and specs
5. **Respect disabled modules** - Keep `webserver.cpp.disabled` disabled until library issues resolved
