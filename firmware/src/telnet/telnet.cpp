#include "telnet.h"
#include <WiFi.h>

WiFiServer telnetServer(23);
WiFiClient telnetClient;

void TelnetServer::init() {
    telnetServer.begin();
    telnetServer.setNoDelay(true);
    
    Serial.println("[TELNET] Server started on port 23");
    Serial2.println("[TELNET] Server started on port 23");
    Serial.printf("[TELNET] Connect with: telnet %s\n", WiFi.localIP().toString().c_str());
    Serial2.printf("[TELNET] Connect with: telnet %s\n", WiFi.localIP().toString().c_str());
}

void TelnetServer::handle() {
    // Check for new client connection
    if (telnetServer.hasClient()) {
        // Disconnect existing client if present
        if (telnetClient && telnetClient.connected()) {
            telnetClient.stop();
        }
        
        telnetClient = telnetServer.available();
        telnetClient.flush();
        
        Serial.println("[TELNET] Client connected");
        Serial2.println("[TELNET] Client connected");
        
        telnetClient.println("\n╔════════════════════════════════════════╗");
        telnetClient.println("║     ESP32-CAM Pantry Helper Console    ║");
        telnetClient.println("╚════════════════════════════════════════╝\n");
        telnetClient.printf("Device ID: %s\n", WiFi.macAddress().c_str());
        telnetClient.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
        telnetClient.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
        telnetClient.println("\nListening to serial output...\n");
    }
    
    // Handle client input (echo for now, could add commands later)
    if (telnetClient && telnetClient.connected() && telnetClient.available()) {
        while (telnetClient.available()) {
            char c = telnetClient.read();
            // Echo back for now - could add command processing here
            Serial.write(c);
        }
    }
}

void TelnetServer::println(const String& message) {
    if (telnetClient && telnetClient.connected()) {
        telnetClient.println(message);
    }
}

void TelnetServer::print(const String& message) {
    if (telnetClient && telnetClient.connected()) {
        telnetClient.print(message);
    }
}
