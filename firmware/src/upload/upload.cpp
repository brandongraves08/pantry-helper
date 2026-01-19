#include "upload.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "../config/config.h"
#include <time.h>

const int MAX_RETRIES = 3;
const int RETRY_DELAY_MS = 2000;
const char *root_ca = 
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDdTCCAl2gAwIBAgILBAAAAAABFUtaw5QwDQYJKoZIhvcNAQEFBQAwVzELMAkG\n"
    "A1UEBhMCQkUxGTAXBgNVBAoTEEdsb2JhbFNpZ24gbnYtc2ExEDAOBgNVBAsTB1Jv\n"
    "b3QgQ0ExGzAZBgNVBAMTEkdsb2JhbFNpZ24gUm9vdCBDQTAeFw05ODA5MDExMjAw\n"
    "MDBaFw0yODAxMjgxMjAwMDBaMFcxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9i\n"
    "YWxTaWduIG52LXNhMRAwDgYDVQQLEwdSb290IENBMRswGQYDVQQDExJHbG9iYWxT\n"
    "aWduIFJvb3QgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDaDuaZ\n"
    "jc6j40+ktiPjxIfnqwhpMlCNr2QQtXSs2RFMnLvnPkM0EY1t9wNnD7RF+67XF1/6\n"
    "9Z73SZnRu7OR6DGxDVItVEBFc5E+YQmrC6DjVITnev/pqsqF/uMh+kT5koj759LK\n"
    "6Ey+UP4YDpkByddbMEisy50jWWGTrtGg1MRRCT7qqO8ledRw35Q+6R2sJT6OfwyY\n"
    "pNmzkBc8kxiV21hdqgOVjOo9UV5slJ8kjrsRsSQSavSji+weUvEGcinqmM9yUjQ\n"
    "vEV4iyGucY5vHaDMsVV7Ygo+2oxcXqNl8zYUUJlmMVfpympXe1d麓jZEgQQvwBAu\n"
    "AgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8EBTADAQH/MB0GA1Ud\n"
    "DgQWBBRge2YaRQ2XyolQL30EzTQo1z8wDQYJKoZIhvcNAQEFBQADggEBAHl9EHfH\n"
    "4bNKbBPV3x8qkdbKUk+RYulYzjLKz5xsNMNlkCEq9yWd9K2OkUnJjgAo3pTYFKAV\n"
    "RGjlUMLWdaGpMx/hnTUZbVBdLFEwmMm3R0MZlp4nO9kZDSJ9YsDRuQhYIqvr/w5h\n"
    "FIpNlhVnQGQj6H5P9S8rrKKpFJf6hL0h7ooFBLzPLV6pDKLrFCrVCfJmJ/TqFkah\n"
    "iVzfRo6b3ydLsIuCbqMXRlZ41BmqPv0tDkJfFhG9yZ7CnSWpS2j8M7vFPQ/6fVwn\n"
    "7sFDf4DYlWkSFfE1XRfJsRLfqNRiS+aUh9RlSW5n3PK1F7iRYCRNxKcM/EJ/lnY=\n"
    "-----END CERTIFICATE-----\n";

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
    
    // Retry logic
    for (int attempt = 0; attempt < MAX_RETRIES; attempt++) {
        if (attempt > 0) {
            Serial.printf("[UPLOAD] Retry attempt %d/%d\n", attempt, MAX_RETRIES);
            delay(RETRY_DELAY_MS);
        }
        
        WiFiClientSecure client;
        client.setCACert(root_ca);
        
        HTTPClient http;
        http.setConnectTimeout(15000);
        http.setTimeout(20000);
        
        // Parse API endpoint
        String endpoint = Config::api_endpoint;
        
        if (!http.begin(client, endpoint)) {
            Serial.println("[UPLOAD] Failed to initialize HTTP");
            continue;
        }
        
        // Generate multipart boundary
        const char *boundary = "----PantryImageBoundary1234567890";
        
        // Build request body
        String body = "";
        
        // Device ID field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"device_id\"\r\n\r\n";
        body += device_id;
        body += "\r\n";
        
        // Timestamp field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"captured_at\"\r\n\r\n";
        body += timestamp_str;
        body += "\r\n";
        
        // Trigger type field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"trigger_type\"\r\n\r\n";
        body += trigger_type;
        body += "\r\n";
        
        // Battery voltage field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"battery_v\"\r\n\r\n";
        body += String(battery_v, 2);
        body += "\r\n";
        
        // RSSI field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"rssi\"\r\n\r\n";
        body += String(rssi);
        body += "\r\n";
        
        // Image file field
        body += "--";
        body += boundary;
        body += "\r\nContent-Disposition: form-data; name=\"image\"; filename=\"capture.jpg\"\r\n";
        body += "Content-Type: image/jpeg\r\n\r\n";
        
        // Prepare headers
        http.addHeader("Content-Type", String("multipart/form-data; boundary=") + boundary);
        http.addHeader("Authorization", String("Bearer ") + Config::api_token);
        
        // Calculate total size
        size_t total_size = body.length() + image_size + strlen(boundary) + 10;
        
        Serial.printf("[UPLOAD] Total payload size: %d bytes\n", total_size);
        Serial.printf("[UPLOAD] Image size: %d bytes\n", image_size);
        
        // Write multipart data
        WiFiClient *stream = http.getStreamPtr();
        if (!stream) {
            Serial.println("[UPLOAD] Failed to get stream");
            http.end();
            continue;
        }
        
        // Write body text part
        stream->write((uint8_t*)body.c_str(), body.length());
        
        // Write image binary data
        stream->write(image_data, image_size);
        
        // Write closing boundary
        String closing = "\r\n--";
        closing += boundary;
        closing += "--\r\n";
        stream->write((uint8_t*)closing.c_str(), closing.length());
        
        // Send POST request
        int httpCode = http.POST("");  // Empty string since we already wrote the body
        
        Serial.printf("[UPLOAD] HTTP response code: %d\n", httpCode);
        
        if (httpCode == 200) {
            String response = http.getString();
            Serial.printf("[UPLOAD] Response: %s\n", response.c_str());
            
            http.end();
            Serial.println("[UPLOAD] Image uploaded successfully!");
            return true;
        } else {
            Serial.printf("[UPLOAD] Upload failed with code %d\n", httpCode);
            http.end();
        }
    }
    
    Serial.println("[UPLOAD] Failed after all retries");
    return false;
}
