#include "power.h"
#include <esp_sleep.h>
#include <driver/gpio.h>
#include <rom/gpio.h>

// Define wakeup pins
#define DOOR_WAKEUP_PIN 33    // GPIO33 - door sensor
#define BATTERY_ADC_PIN 34    // GPIO34 - ADC for battery voltage

void Power::init() {
    Serial.println("[POWER] Initializing power management...");
    
    // Configure GPIO33 for external wakeup
    gpio_config_t io_conf = {};
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = (1ULL << 33);
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
    gpio_config(&io_conf);
    
    // Enable ext0 wakeup on GPIO33 (LOW level)
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_33, 0);
    
    Serial.println("[POWER] Initialized");
}

void Power::deep_sleep(uint32_t duration_ms) {
    Serial.printf("[POWER] Going to sleep for %lu ms\n", duration_ms);
    
    delay(100);  // Flush serial
    
    // Configure timer wakeup
    esp_sleep_enable_timer_wakeup(duration_ms * 1000ULL);  // Convert to microseconds
    
    // Start deep sleep
    esp_deep_sleep_start();
    
    // Never reached
}

uint32_t Power::get_wake_reason() {
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    
    Serial.print("[POWER] Wake reason: ");
    switch(cause) {
        case ESP_SLEEP_WAKEUP_EXT0:
            Serial.println("External signal (EXT0 - GPIO)");
            return 1;  // GPIO wakeup
        case ESP_SLEEP_WAKEUP_TIMER:
            Serial.println("Timer");
            return 2;  // Timer wakeup
        case ESP_SLEEP_WAKEUP_TOUCHPAD:
            Serial.println("Touchpad");
            return 3;
        default:
            Serial.println("Unknown or power-on");
            return 0;
    }
}

// Battery voltage reading
float Battery::read_voltage() {
    // ADC on GPIO34 connected to voltage divider
    // Assuming: Vbatt -> 100k -> ADC(34) -> 100k -> GND
    // So: ADC reads Vbatt/2
    
    int adc_raw = analogRead(BATTERY_ADC_PIN);
    
    // ESP32 ADC resolution: 12-bit (0-4095) -> 0-3.3V
    // Voltage = (adc_raw / 4095.0) * 3.3V
    // Battery voltage = measured_voltage * 2 (due to divider)
    
    float measured_v = (adc_raw / 4095.0) * 3.3;
    float battery_v = measured_v * 2.0;
    
    return battery_v;
}

float Battery::read_percentage() {
    float voltage = read_voltage();
    
    // LiPo battery curve: 3.0V (0%) to 4.2V (100%)
    // With some margin: 2.8V (dead) to 4.3V (charged)
    
    const float MIN_V = 2.8;
    const float MAX_V = 4.3;
    
    if (voltage < MIN_V) return 0.0;
    if (voltage > MAX_V) return 100.0;
    
    float percentage = ((voltage - MIN_V) / (MAX_V - MIN_V)) * 100.0;
    return percentage;
}
