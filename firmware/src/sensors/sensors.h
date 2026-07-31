#pragma once

#include <Arduino.h>

namespace Sensors {
    void init();
    bool check_door();
    bool check_light();
    void debounce();
}
