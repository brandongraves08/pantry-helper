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
    strcpy(Config::settings.ssid, "Mine!");
    strcpy(Config::settings.password, "welcomehome");
    strcpy(Config::settings.device_id, "pantry-cam-001");
    strcpy(Config::settings.api_endpoint, "http://rhel-01.thelab.lan:8000/v1/ingest");
    strcpy(Config::settings.api_token, "QyRNM2kDF8anvaemTJlddemFD5OMcWgErYFImZ7Jx38");
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
