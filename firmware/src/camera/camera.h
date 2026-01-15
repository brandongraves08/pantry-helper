#pragma once

#include <Arduino.h>

namespace Camera {
    void init();
    uint8_t* capture_jpeg();
    void free_image(uint8_t* image_data);
    size_t get_image_size();
}
