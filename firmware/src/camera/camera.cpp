#include "camera.h"
#include "esp_camera.h"
#include "esp_timer.h"

static size_t last_image_size = 0;
static framesize_t framesize = FRAMESIZE_SVGA;  // 800x600
static uint8_t quality = 12;  // JPEG quality (0-63, lower = better)

// Camera pin mapping for ESP32-CAM
#define CAMERA_MODEL_ESP32_CAM_BOARD
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

void Camera::init() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    
    config.xclk_freq_hz = 20000000;  // 20MHz XCLK
    config.frame_size = framesize;
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.jpeg_quality = quality;
    config.fb_count = 1;
    
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[CAMERA] Init failed with error 0x%x\n", err);
        return;
    }
    
    // Optimize camera settings
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_brightness(s, 0);      // brightness
        s->set_contrast(s, 0);         // contrast
        s->set_saturation(s, 0);       // saturation
        s->set_exposure_ctrl(s, 1);    // auto exposure
        s->set_aec2(s, 1);             // auto exposure level
        s->set_gain_ctrl(s, 1);        // auto gain
        s->set_agc_gain(s, 0);         // auto gain level
        s->set_wb_mode(s, 1);          // auto white balance
        s->set_awb_gain(s, 1);         // auto white balance gain
    }
    
    Serial.println("[CAMERA] Initialized successfully");
}

uint8_t* Camera::capture_jpeg() {
    Serial.println("[CAMERA] Capturing JPEG...");
    
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("[CAMERA] Failed to get camera frame buffer");
        return nullptr;
    }
    
    // Store size
    last_image_size = fb->len;
    
    // Allocate buffer and copy data
    uint8_t *image_data = (uint8_t *)malloc(fb->len);
    if (!image_data) {
        Serial.println("[CAMERA] Failed to allocate memory for image");
        esp_camera_fb_return(fb);
        return nullptr;
    }
    
    memcpy(image_data, fb->buf, fb->len);
    esp_camera_fb_return(fb);
    
    Serial.printf("[CAMERA] Captured JPEG: %d bytes\n", last_image_size);
    return image_data;
}

void Camera::free_image(uint8_t* image_data) {
    if (image_data) {
        free(image_data);
    }
}

size_t Camera::get_image_size() {
    return last_image_size;
}
