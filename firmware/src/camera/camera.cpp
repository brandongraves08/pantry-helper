#include "camera.h"

static size_t last_image_size = 0;

void Camera::init() {
    // TODO: Initialize OV2640 or similar camera module
    // ESP32-CAM specific:
    // - Configure camera pins (SIOD, SIOC, VSYNC, HREF, PCLK, D0-D7, XCLK)
    // - Set resolution, frame rate, quality
    Serial.println("[CAMERA] Initialized");
}

uint8_t* Camera::capture_jpeg() {
    // TODO: Capture frame from camera and encode to JPEG
    // Return pointer to JPEG buffer
    // Store size in last_image_size
    Serial.println("[CAMERA] Capturing JPEG...");
    return nullptr;  // Placeholder
}

void Camera::free_image(uint8_t* image_data) {
    if (image_data) {
        free(image_data);
    }
}

size_t Camera::get_image_size() {
    return last_image_size;
}
