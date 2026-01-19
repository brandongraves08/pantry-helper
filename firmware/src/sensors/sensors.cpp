#include "sensors.h"

// GPIO pin assignments for ESP32-CAM
const int DOOR_PIN = 33;        // Reed switch (GPIO33)
const int LIGHT_PIN = 34;       // Analog light sensor (GPIO34 - ADC1_CH6)

// Sensor thresholds and timing
const int LIGHT_THRESHOLD = 100;       // ADC value threshold for light
const unsigned long DEBOUNCE_MS = 50;  // Debounce delay (ms)
const unsigned long QUIET_PERIOD_MS = 30000;  // Quiet period after trigger (30s)

// Sensor state tracking
static unsigned long last_door_change = 0;
static unsigned long last_light_change = 0;
static unsigned long last_trigger_time = 0;
static bool last_door_state = true;  // true = closed (HIGH), false = open (LOW)
static bool last_light_state = false;
static int light_value_history[5] = {0};  // Keep history for smoothing

void Sensors::init() {
    Serial.println("[SENSORS] Initializing sensor pins...");
    
    pinMode(DOOR_PIN, INPUT_PULLUP);
    pinMode(LIGHT_PIN, INPUT);
    
    // Initialize sensor states
    last_door_state = digitalRead(DOOR_PIN);
    last_light_state = analogRead(LIGHT_PIN) > LIGHT_THRESHOLD;
    
    Serial.printf("[SENSORS] Door pin: GPIO%d\n", DOOR_PIN);
    Serial.printf("[SENSORS] Light pin: GPIO%d (threshold: %d)\n", LIGHT_PIN, LIGHT_THRESHOLD);
    Serial.println("[SENSORS] Initialized");
}

bool Sensors::check_door() {
    bool current_door_state = digitalRead(DOOR_PIN);
    
    // Check for state change
    if (current_door_state != last_door_state) {
        // State changed, check debounce
        if (millis() - last_door_change > DEBOUNCE_MS) {
            last_door_state = current_door_state;
            last_door_change = millis();
            
            if (!current_door_state) {  // Door opened (LOW)
                Serial.println("[SENSORS] Door opened!");
                
                // Check quiet period
                if (millis() - last_trigger_time > QUIET_PERIOD_MS) {
                    last_trigger_time = millis();
                    return true;
                } else {
                    Serial.println("[SENSORS] Door trigger ignored (quiet period)");
                }
            } else {
                Serial.println("[SENSORS] Door closed");
            }
        }
    } else {
        // Reset debounce timer if state stable
        last_door_change = millis();
    }
    
    return false;
}

bool Sensors::check_light() {
    // Read analog light sensor
    int raw_light = analogRead(LIGHT_PIN);
    
    // Shift history and add new reading
    for (int i = 4; i > 0; i--) {
        light_value_history[i] = light_value_history[i-1];
    }
    light_value_history[0] = raw_light;
    
    // Calculate moving average (smoothing)
    int avg_light = 0;
    for (int i = 0; i < 5; i++) {
        avg_light += light_value_history[i];
    }
    avg_light /= 5;
    
    bool current_light_state = avg_light > LIGHT_THRESHOLD;
    
    // Check for state change (light turned on)
    if (current_light_state != last_light_state) {
        if (millis() - last_light_change > DEBOUNCE_MS) {
            last_light_state = current_light_state;
            last_light_change = millis();
            
            if (current_light_state) {  // Light turned ON
                Serial.printf("[SENSORS] Light turned ON (value: %d)\n", avg_light);
                
                // Check quiet period
                if (millis() - last_trigger_time > QUIET_PERIOD_MS) {
                    last_trigger_time = millis();
                    return true;
                } else {
                    Serial.println("[SENSORS] Light trigger ignored (quiet period)");
                }
            } else {
                Serial.printf("[SENSORS] Light turned OFF (value: %d)\n", avg_light);
            }
        }
    } else {
        // Reset debounce timer if state stable
        last_light_change = millis();
    }
    
    return false;
}

void Sensors::debounce() {
    // Debounce logic is integrated into individual sensor checks
    // This is a no-op, kept for API compatibility
}
