#include "upload.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "../config/config.h"
#include <time.h>

const int MAX_RETRIES = 3;
const int RETRY_DELAY_MS = 2000;

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
    
    // Generate ISO8601 timestamp
    char timestamp_str[32];
    struct tm *timeinfo = localtime(&timestamp);
    strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
    
    // Build multipart body in memory
    // NOTE: For large images (VGA+ JPEG at 50-100KB), building in RAM is fine.
    // For full 5MP captures, consider using a streaming approach instead.
    
    const char *boundary = "----PantryImageBoundary1234567890";
    
    // Calculate sizes for each part (text fields)
    String text_fields = "";
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
    text_fields += device_id;
    text_fields += "\r\n";
    
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n";
    text_fields += timestamp_str;
    text_fields += "\r\n";
    
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"trigger_type\"\r\n\r\n";
    text_fields += trigger_type;
    text_fields += "\r\n";
    
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"battery_v\"\r\n\r\n";
    text_fields += String(battery_v, 2);
    text_fields += "\r\n";
    
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"rssi\"\r\n\r\n";
    text_fields += String(rssi);
    text_fields += "\r\n";
    
    text_fields += "--" + String(boundary) + "\r\n";
    text_fields += "Content-Disposition: form-data; name=\"image\"; filename=\"capture.jpg\"\r\n";
    text_fields += "Content-Type: image/jpeg\r\n\r\n";
    
    String closing_boundary = "\r\n--" + String(boundary) + "--\r\n";
    
    size_t full_size = text_fields.length() + image_size + closing_boundary.length();
    
    // Allocate full body buffer
    uint8_t* full_body = (uint8_t*)malloc(full_size);
    if (!full_body) {
        Serial.println("[UPLOAD] Failed to allocate memory for request body");
        return false;
    }
    
    size_t offset = 0;
    memcpy(full_body + offset, text_fields.c_str(), text_fields.length());
    offset += text_fields.length();
    memcpy(full_body + offset, image_data, image_size);
    offset += image_size;
    memcpy(full_body + offset, closing_boundary.c_str(), closing_boundary.length());
    offset += closing_boundary.length();
    
    // Retry logic
    for (int attempt = 0; attempt < MAX_RETRIES; attempt++) {
        if (attempt > 0) {
            Serial.printf("[UPLOAD] Retry attempt %d/%d\n", attempt + 1, MAX_RETRIES);
            delay(RETRY_DELAY_MS);
        }
        
        WiFiClientSecure client;
        // Disable cert verification for development — API uses HTTP in config
        // For production, remove this line and use a valid CA cert
        client.setInsecure();
        
        HTTPClient http;
        http.setConnectTimeout(15000);
        http.setTimeout(30000);
        
        String endpoint = Config::api_endpoint;
        
        if (!http.begin(client, endpoint)) {
            Serial.println("[UPLOAD] Failed to initialize HTTP");
            continue;
        }
        
        String content_type = String("multipart/form-data; boundary=") + boundary;
        http.addHeader("Content-Type", content_type);
        http.addHeader("Authorization", String("Bearer ") + Config::api_token);
        
        Serial.printf("[UPLOAD] Sending %d bytes...\n", full_size);
        
        int httpCode = http.POST(full_body, full_size);
        
        Serial.printf("[UPLOAD] HTTP response code: %d\n", httpCode);
        
        if (httpCode > 0) {
            if (httpCode == 200 || httpCode == 201) {
                String response = http.getString();
                Serial.printf("[UPLOAD] Response: %s\n", response.c_str());
                http.end();
                free(full_body);
                Serial.println("[UPLOAD] Image uploaded successfully!");
                return true;
            } else {
                String error_body = http.getString();
                Serial.printf("[UPLOAD] Server error (%d): %s\n", httpCode, error_body.c_str());
            }
        } else {
            Serial.printf("[UPLOAD] Connection error: %d\n", httpCode);
        }
        
        http.end();
    }
    
    free(full_body);
    Serial.println("[UPLOAD] Failed after all retries");
    return false;
}
