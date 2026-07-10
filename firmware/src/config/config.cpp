#include "config.h"
#include <cstring>

Config::Settings Config::settings;

// Static pointers to settings
char* Config::ssid = Config::settings.ssid;
char* Config::password = Config::settings.password;
char* Config::device_id = Config::settings.device_id;
char* Config::api_endpoint = Config::settings.api_endpoint;
char* Config::api_token = Config::settings.api_token;

void Config::_init_defaults() {
    // Initialize settings with defaults
    // WARNING: These are placeholders. Configure via NVS/EEPROM in production.
    strcpy(Config::settings.ssid, "IoT");
    strcpy(Config::settings.password, "getoffmynetwork");
    strcpy(Config::settings.device_id, "pantry-cam-001");
    strcpy(Config::settings.api_endpoint, "http://192.168.2.143:8081/v1/ingest");
    strcpy(Config::settings.api_token, "BXV5udbHWF8e5JvrtQ8fZgTHkqEq4XaosOZXLCx5_-A");
    Config::settings.light_threshold = 100;
    Config::settings.quiet_period_ms = 30000;
}

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
