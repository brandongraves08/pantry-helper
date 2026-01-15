#include "upload.h"
#include <WiFiClientSecure.h>
#include "../config/config.h"

bool Upload::send_image(
    const uint8_t* image_data,
    size_t image_size,
    const char* device_id,
    time_t timestamp,
    const char* trigger_type,
    float battery_v,
    int rssi
) {
    Serial.println("[UPLOAD] Preparing request...");
    
    // TODO: Implement multipart/form-data POST with:
    // - image file
    // - device_id
    // - timestamp (ISO8601)
    // - trigger_type
    // - battery_v
    // - rssi
    
    // Pseudocode:
    // - Create WiFiClientSecure connection
    // - Build multipart boundary
    // - Write headers, form fields, image data
    // - Handle response (should be 200 with capture_id in JSON)
    // - Return success/failure
    
    Serial.println("[UPLOAD] Request complete");
    return true;  // Placeholder
}
