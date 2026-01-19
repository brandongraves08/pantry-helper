#include <Arduino.h>
#include <time.h>
#include "config/config.h"
#include "power/power.h"
#include "sensors/sensors.h"
#include "camera/camera.h"
#include "net/wifi_manager.h"
#include "upload/upload.h"

// System state
volatile bool woken_by_door = false;
volatile bool woken_by_light = false;
volatile bool image_captured = false;
volatile uint8_t* captured_image = nullptr;
volatile size_t captured_image_size = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n╔════════════════════════════════════════╗");
    Serial.println("║     PANTRY CAMERA SYSTEM STARTING      ║");
    Serial.println("║         Phase 4: Full Firmware         ║");
    Serial.println("╚════════════════════════════════════════╝\n");
    
    // Initialize configuration
    Serial.println("[SETUP] Loading configuration...");
    Config::load();
    Serial.printf("[SETUP] Device ID: %s\n", Config::device_id);
    
    // Initialize subsystems
    Serial.println("[SETUP] Initializing power management...");
    Power::init();
    
    Serial.println("[SETUP] Initializing sensors...");
    Sensors::init();
    
    Serial.println("[SETUP] Initializing camera...");
    Camera::init();
    
    // Print wake reason
    uint32_t wake_reason = Power::get_wake_reason();
    Serial.printf("[SETUP] Wake reason: %lu\n", wake_reason);
    
    // Print battery status
    float battery_v = Battery::read_voltage();
    float battery_pct = Battery::read_percentage();
    Serial.printf("[SETUP] Battery: %.2fV (%.1f%%)\n", battery_v, battery_pct);
    
    Serial.println("[SETUP] ✓ All systems initialized\n");
    Serial.println("═══════════════════════════════════════\n");
}

void loop() {
    // Check for triggers
    if (Sensors::check_door()) {
        Serial.println("\n[MAIN] Door trigger detected!");
        handle_capture_event("door");
    } 
    else if (Sensors::check_light()) {
        Serial.println("\n[MAIN] Light trigger detected!");
        handle_capture_event("light");
    }
    
    // Keep loop responsive
    delay(100);
}

void handle_capture_event(const char* trigger_type) {
    Serial.println("[EVENT] ════════════════════════════════════");
    Serial.printf("[EVENT] Capture triggered by: %s\n", trigger_type);
    Serial.println("[EVENT] ════════════════════════════════════\n");
    
    // Step 1: Capture image
    Serial.println("[EVENT] Step 1: Capturing image...");
    uint8_t* image_data = Camera::capture_jpeg();
    if (!image_data) {
        Serial.println("[ERROR] Failed to capture image - retrying...");
        delay(500);
        image_data = Camera::capture_jpeg();
        if (!image_data) {
            Serial.println("[ERROR] Capture failed twice - aborting");
            return;
        }
    }
    
    size_t image_size = Camera::get_image_size();
    Serial.printf("[EVENT] ✓ Image captured: %d bytes\n\n", image_size);
    
    // Step 2: Get current time
    Serial.println("[EVENT] Step 2: Synchronizing time...");
    time_t now = time(nullptr);
    if (now < 1000) {
        Serial.println("[WARNING] Time not set, attempting NTP sync...");
        // TODO: Add NTP time sync if needed
        now = millis() / 1000;  // Use uptime as fallback
    }
    Serial.printf("[EVENT] ✓ Current timestamp: %lu\n\n", now);
    
    // Step 3: Collect metadata
    Serial.println("[EVENT] Step 3: Collecting metadata...");
    float battery_v = Battery::read_voltage();
    float battery_pct = Battery::read_percentage();
    int rssi = 0;  // Will update after WiFi connect
    Serial.printf("[EVENT] Battery: %.2fV (%.1f%%)\n", battery_v, battery_pct);
    
    // Step 4: Connect to WiFi
    Serial.println("\n[EVENT] Step 4: Connecting to WiFi...");
    if (!WiFiManager::connect(Config::ssid, Config::password, 15000)) {
        Serial.println("[ERROR] WiFi connection failed - will retry next wakeup");
        Camera::free_image(image_data);
        return;
    }
    rssi = WiFiManager::get_rssi();
    Serial.printf("[EVENT] ✓ WiFi connected, RSSI: %d dBm\n\n", rssi);
    
    // Step 5: Upload image
    Serial.println("[EVENT] Step 5: Uploading image to backend...");
    Serial.printf("[EVENT] API endpoint: %s\n", Config::api_endpoint);
    
    bool upload_success = Upload::send_image(
        image_data,
        image_size,
        Config::device_id,
        now,
        trigger_type,
        battery_v,
        rssi
    );
    
    if (upload_success) {
        Serial.println("\n[EVENT] ✓ Upload successful!");
    } else {
        Serial.println("\n[ERROR] Upload failed - will retry next wakeup");
    }
    
    // Cleanup
    Camera::free_image(image_data);
    WiFiManager::disconnect();
    
    Serial.println("\n[EVENT] ════════════════════════════════════");
    Serial.println("[EVENT] Cycle complete - returning to deep sleep\n\n");
    
    // Step 6: Return to deep sleep
    Serial.println("[SLEEP] Entering deep sleep mode...");
    Serial.println("[SLEEP] Device will wake on:");
    Serial.println("[SLEEP]   - Door sensor (GPIO33) going LOW");
    Serial.println("[SLEEP]   - Timer interrupt (periodic fallback)\n");
    
    delay(500);  // Give time for serial to flush
    Power::deep_sleep(Config::quiet_period_ms);
}
