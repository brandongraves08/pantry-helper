#include "wifi_manager.h"
#include <WiFi.h>

bool WiFiManager::connect(const char* ssid, const char* password, uint32_t timeout_ms) {
    Serial.printf("[WIFI] Connecting to %s\n", ssid);
    Serial2.printf("[WIFI] Connecting to %s\n", ssid);
    
    // If already connected, return success
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[WIFI] Already connected");
        Serial2.println("[WIFI] Already connected");
        return true;
    }
    
    // Disconnect first to ensure clean state
    WiFi.disconnect(true);
    delay(100);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - start > timeout_ms) {
            Serial.println("[WIFI] Connection timeout");
            Serial2.println("[WIFI] Connection timeout");
            Serial.printf("[WIFI] Status: %d\n", WiFi.status());
            Serial2.printf("[WIFI] Status: %d\n", WiFi.status());
            return false;
        }
        delay(100);
        Serial.print(".");
    }
    
    Serial.printf("\n[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    Serial2.printf("\n[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    return true;
}

void WiFiManager::disconnect() {
    WiFi.disconnect(true);  // Turn off WiFi radio
    Serial.println("[WIFI] Disconnected");
    Serial2.println("[WIFI] Disconnected");
}

int WiFiManager::get_rssi() {
    return WiFi.RSSI();
}
