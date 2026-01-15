#pragma once

#include <Arduino.h>

namespace Config {
    struct Settings {
        char ssid[64];
        char password[64];
        char device_id[64];
        char api_endpoint[256];
        char api_token[256];
        uint16_t light_threshold;
        uint32_t quiet_period_ms;
    };
    
    extern Settings settings;
    
    // Quick access
    extern char* ssid;
    extern char* password;
    extern char* device_id;
    extern char* api_endpoint;
    extern char* api_token;
    
    void load();
    void save();
    void reset_to_defaults();
}
