#include "config.h"

Config::Settings Config::settings = {
    .ssid = "YOUR_SSID",
    .password = "YOUR_PASSWORD",
    .device_id = "pantry-cam-001",
    .api_endpoint = "https://api.example.com/v1/ingest",
    .api_token = "your-device-token-here",
    .light_threshold = 100,
    .quiet_period_ms = 30000,
};

char* Config::ssid = Config::settings.ssid;
char* Config::password = Config::settings.password;
char* Config::device_id = Config::settings.device_id;
char* Config::api_endpoint = Config::settings.api_endpoint;
char* Config::api_token = Config::settings.api_token;

void Config::load() {
    // TODO: Load from EEPROM/NVS
    Serial.println("[CONFIG] Using default settings");
}

void Config::save() {
    // TODO: Save to EEPROM/NVS
    Serial.println("[CONFIG] Settings saved");
}

void Config::reset_to_defaults() {
    // Reset struct to default values
}
