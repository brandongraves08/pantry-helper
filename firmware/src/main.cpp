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

// Deep sleep duration when no trigger is active (30 seconds)
const uint32_t SLEEP_INTERVAL_MS = 30000;
// Maximum wake time before forced sleep (25 seconds)
const uint32_t MAX_WAKE_MS = 25000;

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial2.begin(115200);
    delay(500);
    
    Serial.println("\r\n\r\n=== ESP32 Pantry Cam Boot ===");
    Serial2.println("\r\n\r\n=== ESP32 Pantry Cam Boot ===");
    
    // Initialize modules
    Power::init();
    Sensors::init();
    
    // Check why we woke up
    uint32_t wake_reason = Power::get_wake_reason();
    
    bool do_capture = false;
    const char* trigger = "timer";
    
    if (wake_reason == 1) {  // GPIO (door sensor)
        Serial.println("[MAIN] Woke from door sensor");
        Serial2.println("[MAIN] Woke from door sensor");
        trigger = "door";
        
        // Check if door actually opened (debounce handled in sensor)
        if (Sensors::check_door()) {
            do_capture = true;
        }
    } else if (wake_reason == 2) {  // Timer
        Serial.println("[MAIN] Woke from timer");
        Serial2.println("[MAIN] Woke from timer");
        
        // Check if pantry light is on
        if (Sensors::check_light()) {
            do_capture = true;
            trigger = "light";
        } else {
            // Timer wake but no light — could do periodic check
            // For now, skip capture if no light (pantry is dark)
            Serial.println("[MAIN] No light detected, skipping capture");
            Serial2.println("[MAIN] No light detected, skipping capture");
        }
    } else {  // Power-on or unknown
        Serial.println("[MAIN] Power-on boot — taking initial capture");
        Serial2.println("[MAIN] Power-on boot — taking initial capture");
        do_capture = true;
        trigger = "boot";
    }
    
    if (do_capture) {
        Serial.println("[MAIN] Triggering capture...");
        Serial2.println("[MAIN] Triggering capture...");
        
        // Connect WiFi with timeout
        if (WiFiManager::connect(Config::ssid, Config::password, 15000)) {
            Serial.printf("[MAIN] WiFi connected! IP: %s, RSSI: %d dBm\n",
                WiFi.localIP().toString().c_str(), WiFi.RSSI());
            
            // Initialize camera
            Camera::init();
            delay(300);
            
            // Capture image
            uint8_t* image_data = Camera::capture_jpeg();
            size_t image_size = Camera::get_image_size();
            
            if (image_data != nullptr && image_size > 0) {
                float battery_v = Battery::read_voltage();
                int rssi = WiFi.RSSI();
                
                // Upload image
                if (Upload::send_image(image_data, image_size,
                        Config::device_id, time(nullptr),
                        trigger, battery_v, rssi)) {
                    Serial.println("[MAIN] Capture and upload successful!");
                    Serial2.println("[MAIN] Capture and upload successful!");
                } else {
                    Serial.println("[MAIN] Upload failed");
                    Serial2.println("[MAIN] Upload failed");
                }
                
                Camera::free_image(image_data);
            } else {
                Serial.println("[MAIN] Camera capture failed");
                Serial2.println("[MAIN] Camera capture failed");
            }
        } else {
            Serial.println("[MAIN] WiFi connection failed");
            Serial2.println("[MAIN] WiFi connection failed");
        }
        
        // Disconnect WiFi to save power
        WiFiManager::disconnect();
    }
    
    Serial.println("[MAIN] Going to deep sleep...");
    Serial2.println("[MAIN] Going to deep sleep...");
    delay(100);  // Flush serial before sleep
    
    // Enter deep sleep (timer wake for periodic check + GPIO wake for door)
    Power::deep_sleep(SLEEP_INTERVAL_MS);
}

void loop() {
    // Never reached — ESP32 goes to deep sleep in setup()
}
