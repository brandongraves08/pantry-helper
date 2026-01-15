#include "wifi_manager.h"
#include <WiFi.h>

bool WiFiManager::connect(const char* ssid, const char* password, uint32_t timeout_ms) {
    Serial.printf("[WIFI] Connecting to %s\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - start > timeout_ms) {
            Serial.println("[WIFI] Connection timeout");
            return false;
        }
        delay(100);
    }
    
    Serial.printf("[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    return true;
}

void WiFiManager::disconnect() {
    WiFi.disconnect(true);  // Turn off WiFi radio
    Serial.println("[WIFI] Disconnected");
}

int WiFiManager::get_rssi() {
    return WiFi.RSSI();
}
