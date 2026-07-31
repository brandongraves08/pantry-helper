#pragma once

#include <Arduino.h>

namespace WiFiManager {
    bool connect(const char* ssid, const char* password, uint32_t timeout_ms);
    void disconnect();
    int get_rssi();
}
