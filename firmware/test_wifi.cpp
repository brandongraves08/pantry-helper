#include <Arduino.h>
#include <WiFi.h>

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("\n\n=== WiFi Test ===");
    Serial.println("Scanning for networks...");
    
    int n = WiFi.scanNetworks();
    Serial.printf("Found %d networks:\n", n);
    
    bool found_mine = false;
    for (int i = 0; i < n; i++) {
        Serial.printf("%d: %s (RSSI: %d)\n", i+1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));
        if (WiFi.SSID(i) == "Mine!") {
            found_mine = true;
        }
    }
    
    Serial.println();
    if (found_mine) {
        Serial.println("✓ Network 'Mine!' found!");
        Serial.println("\nAttempting connection...");
        
        WiFi.mode(WIFI_STA);
        WiFi.begin("Mine!", "welcomehome");
        
        int attempts = 0;
        while (WiFi.status() != WL_CONNECTED && attempts < 20) {
            delay(500);
            Serial.print(".");
            attempts++;
        }
        
        Serial.println();
        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("✓ Connected!");
            Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
            Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
        } else {
            Serial.println("✗ Connection failed");
            Serial.printf("Status: %d\n", WiFi.status());
        }
    } else {
        Serial.println("✗ Network 'Mine!' NOT found");
        Serial.println("Check if the SSID is correct and router is powered on");
    }
}

void loop() {
    delay(1000);
}
