#pragma once

#include <Arduino.h>

namespace Power {
    void init();
    void deep_sleep(uint32_t duration_ms);
    uint32_t get_wake_reason();
}

namespace Battery {
    float read_voltage();
    float read_percentage();
}
