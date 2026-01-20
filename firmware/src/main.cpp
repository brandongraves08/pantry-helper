#include <Arduino.h>
#include <WiFi.h>
#include <time.h>
#include "config/config.h"
#include "power/power.h"
#include "sensors/sensors.h"
#include "camera/camera.h"
#include "net/wifi_manager.h"
#include "upload/upload.h"
//#include "webserver/webserver.h"  // Disabled - library issues
#include "ota/ota.h"
#include "telnet/telnet.h"

// Use Serial2 on UART2 (GPIO16 RX, GPIO17 TX) to avoid conflict with camera
// Serial is on UART0 (GPIO1/3) which conflicts with camera module

void setup() {
    // Minimal setup - just print and init WiFi
    delay(500);
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\r\n\r\n=== ESP32 BOOT ===");
    Serial.printf("Setup starting... Heap free: %u\n", ESP.getFreeHeap());
    
    // Try WiFi connection right away
    Serial.println("Starting WiFi...");
    WiFi.mode(WIFI_STA);
    WiFi.begin("Mine!", "welcomehome");
    
    Serial.println("Waiting for WiFi...");
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\nWiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
        Serial.println("Starting OTA...");
        OTA::init();
        Serial.println("Starting Telnet...");
        TelnetServer::init();
        Serial.println("Remote services started!");
    } else {
        Serial.println("\nWiFi failed");
    }
    
    Serial.println("Setup complete");
}

static bool first_boot = true;
static unsigned long last_capture_time = 0;
static bool remote_services_started = false;
const unsigned long CAPTURE_INTERVAL_MS = 60000;  // 1 minute

void handle_capture_event(const char* trigger_type) {
    // Handle a capture trigger event
    String msg = String("\n[CAPTURE] Triggered by: ") + trigger_type;
    Serial.println(msg);
    Serial2.println(msg);
    TelnetServer::println(msg);
    //WebServer::add_log(msg);
    Serial.flush();
    Serial2.flush();
    
    msg = "[CAPTURE] → Connecting WiFi...";
    Serial.println(msg);
    Serial2.println(msg);
    TelnetServer::println(msg);
    //WebServer::add_log(msg);
    Serial.flush();
    Serial2.flush();
    
    // Connect to WiFi (if not already connected)
    if (!WiFiManager::connect(Config::ssid, Config::password, 15000)) {
        msg = "[CAPTURE] ✗ WiFi connection failed";
        Serial.println(msg);
        Serial2.println(msg);
        TelnetServer::println(msg);
        //WebServer::add_log(msg);
        Serial.flush();
        Serial2.flush();
        return;
    }
    
    // Start remote services if not already started
    if (!remote_services_started) {
        //WebServer::init();
        OTA::init();
        TelnetServer::init();
        remote_services_started = true;
        //WebServer::add_log("[REMOTE] All remote services started");
    }
    
    msg = "[CAPTURE] → WiFi connected!";
    Serial.println(msg);
    Serial2.println(msg);
    TelnetServer::println(msg);
    //WebServer::add_log(msg);
    
    msg = String("[CAPTURE] → RSSI: ") + WiFiManager::get_rssi() + " dBm";
    Serial.println(msg);
    Serial2.println(msg);
    TelnetServer::println(msg);
    //WebServer::add_log(msg);
    Serial.flush();
    Serial2.flush();
    
    // For now, create a dummy image or skip actual camera capture
    // TODO: Integrate actual camera capture
    uint8_t dummy_image[] = {0xFF, 0xD8, 0xFF, 0xE0};  // JPEG header
    size_t image_size = sizeof(dummy_image);
    
    float battery_v = Battery::read_voltage();
    int rssi = WiFiManager::get_rssi();
    
    msg = "[CAPTURE] → Uploading image to backend...";
    Serial.println(msg);
    Serial2.println(msg);
    TelnetServer::println(msg);
    //WebServer::add_log(msg);
    Serial.flush();
    Serial2.flush();
    
    if (Upload::send_image(dummy_image, image_size, Config::device_id, time(nullptr), trigger_type, battery_v, rssi)) {
        msg = "[CAPTURE] ✓ Upload successful!";
        Serial.println(msg);
        Serial2.println(msg);
        TelnetServer::println(msg);
        //WebServer::add_log(msg);
    } else {
        msg = "[CAPTURE] ✗ Upload failed!";
        Serial.println(msg);
        Serial2.println(msg);
        TelnetServer::println(msg);
        //WebServer::add_log(msg);
    }
    
    Serial.flush();
    Serial2.flush();
    
    // Note: Keep WiFi connected for remote access
    // WiFi will stay on for web server, OTA, and telnet access
}

void loop() {
    unsigned long now = millis();
    
    // Handle remote services if WiFi is connected
    if (WiFi.status() == WL_CONNECTED && remote_services_started) {
        OTA::handle();
        TelnetServer::handle();
        //WebServer::handle();
    }
    
    // Capture on first boot
    if (first_boot) {
        delay(2000);
        Serial.println("\n[MAIN] ═══════════════════════════════════════");
        Serial.println("[MAIN] Boot capture triggered!");
        Serial.println("[MAIN] ═══════════════════════════════════════");
        Serial2.println("\n[MAIN] ═══════════════════════════════════════");
        Serial2.println("[MAIN] Boot capture triggered!");
        Serial2.println("[MAIN] ═══════════════════════════════════════");
        Serial.flush();
        Serial2.flush();
        first_boot = false;
        last_capture_time = now;
        handle_capture_event("boot");
    }
    
    // Capture every minute
    if (now - last_capture_time > CAPTURE_INTERVAL_MS) {
        last_capture_time = now;
        Serial.println("\n[MAIN] ═══════════════════════════════════════");
        Serial.println("[MAIN] Periodic capture triggered (1 minute interval)!");
        Serial.println("[MAIN] ═══════════════════════════════════════");
        Serial2.println("\n[MAIN] ═══════════════════════════════════════");
        Serial2.println("[MAIN] Periodic capture triggered (1 minute interval)!");
        Serial2.println("[MAIN] ═══════════════════════════════════════");
        Serial.flush();
        Serial2.flush();
        handle_capture_event("timer");
    }
    
    // Keep loop responsive
    delay(100);
}
