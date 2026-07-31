#pragma once

#include <Arduino.h>
#include <time.h>

namespace Upload {
    bool send_image(
        const uint8_t* image_data,
        size_t image_size,
        const char* device_id,
        time_t timestamp,
        const char* trigger_type,
        float battery_v,
        int rssi
    );
}
