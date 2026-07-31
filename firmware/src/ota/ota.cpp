#include "ota.h"
#include <ArduinoOTA.h>
#include <WiFi.h>
#include "../config/config.h"

void OTA::init() {
    ArduinoOTA.setHostname(Config::device_id);
    ArduinoOTA.setPassword("pantry2026");  // OTA password for security
    
    ArduinoOTA.onStart([]() {
        String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
        Serial.println("\n[OTA] Start updating " + type);
        Serial2.println("\n[OTA] Start updating " + type);
    });
    
    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] Update complete!");
        Serial2.println("\n[OTA] Update complete!");
    });
    
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        unsigned int percent = (progress / (total / 100));
        Serial.printf("[OTA] Progress: %u%%\r", percent);
        Serial2.printf("[OTA] Progress: %u%%\r", percent);
    });
    
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("\n[OTA] Error[%u]: ", error);
        Serial2.printf("\n[OTA] Error[%u]: ", error);
        
        if (error == OTA_AUTH_ERROR) {
            Serial.println("Auth Failed");
            Serial2.println("Auth Failed");
        } else if (error == OTA_BEGIN_ERROR) {
            Serial.println("Begin Failed");
            Serial2.println("Begin Failed");
        } else if (error == OTA_CONNECT_ERROR) {
            Serial.println("Connect Failed");
            Serial2.println("Connect Failed");
        } else if (error == OTA_RECEIVE_ERROR) {
            Serial.println("Receive Failed");
            Serial2.println("Receive Failed");
        } else if (error == OTA_END_ERROR) {
            Serial.println("End Failed");
            Serial2.println("End Failed");
        }
    });
    
    ArduinoOTA.begin();
    
    Serial.println("[OTA] Ready for updates");
    Serial2.println("[OTA] Ready for updates");
    Serial.printf("[OTA] IP: %s\n", WiFi.localIP().toString().c_str());
    Serial2.printf("[OTA] IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.println("[OTA] Upload with: platformio run -t upload --upload-port " + WiFi.localIP().toString());
    Serial2.println("[OTA] Upload with: platformio run -t upload --upload-port " + WiFi.localIP().toString());
}

void OTA::handle() {
    ArduinoOTA.handle();
}
