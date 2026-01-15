#include "power.h"

void Power::init() {
    // Configure RTC memory, wakeup sources, etc.
    Serial.println("[POWER] Initialized");
}

void Power::deep_sleep(uint32_t duration_ms) {
    Serial.printf("[POWER] Going to sleep for %lu ms\n", duration_ms);
    delay(100);  // Flush serial
    esp_sleep_enable_timer_wakeup(duration_ms * 1000);  // Convert to microseconds
    esp_deep_sleep_start();
}

uint32_t Power::get_wake_reason() {
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    return (uint32_t)cause;
}

float Battery::read_voltage() {
    // TODO: Read ADC pin connected to voltage divider
    return 4.2f;
}

float Battery::read_percentage() {
    float voltage = read_voltage();
    // Approximate: 3.0V = 0%, 4.2V = 100%
    return (voltage - 3.0f) / (4.2f - 3.0f) * 100.0f;
}
