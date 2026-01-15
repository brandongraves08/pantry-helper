#include <Arduino.h>
#include "config/config.h"
#include "power/power.h"
#include "sensors/sensors.h"
#include "camera/camera.h"
#include "net/wifi_manager.h"
#include "upload/upload.h"

// Global state
volatile bool woken_by_door = false;
volatile bool woken_by_light = false;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n[PANTRY] Starting Pantry Camera System");
    
    // Initialize subsystems
    Config::load();
    Power::init();
    Sensors::init();
    Camera::init();
    
    Serial.println("[PANTRY] Setup complete. Entering main loop.");
}

void loop() {
    // Check for wake triggers
    if (Sensors::check_door()) {
        Serial.println("[PANTRY] Door trigger detected!");
        handle_capture_event("door");
    } else if (Sensors::check_light()) {
        Serial.println("[PANTRY] Light trigger detected!");
        handle_capture_event("light");
    }
    
    // Sleep between checks
    delay(100);
}

void handle_capture_event(const char* trigger_type) {
    Serial.println("[PANTRY] Capturing image...");
    
    // Capture image
    uint8_t* image_data = Camera::capture_jpeg();
    if (!image_data) {
        Serial.println("[ERROR] Failed to capture image");
        return;
    }
    
    // Connect to WiFi
    Serial.println("[PANTRY] Connecting to WiFi...");
    if (!WiFiManager::connect(Config::ssid, Config::password, 15000)) {
        Serial.println("[ERROR] WiFi connection failed");
        Camera::free_image(image_data);
        return;
    }
    
    // Get current time
    time_t now = time(nullptr);
    
    // Upload to backend
    Serial.println("[PANTRY] Uploading to backend...");
    bool success = Upload::send_image(
        image_data,
        Camera::get_image_size(),
        Config::device_id,
        now,
        trigger_type,
        Battery::read_voltage(),
        WiFiManager::get_rssi()
    );
    
    if (success) {
        Serial.println("[PANTRY] Upload successful!");
    } else {
        Serial.println("[ERROR] Upload failed");
    }
    
    // Cleanup
    Camera::free_image(image_data);
    WiFiManager::disconnect();
    
    // Return to sleep
    Serial.println("[PANTRY] Returning to deep sleep...");
    Power::deep_sleep(Config::quiet_period_ms);
}
