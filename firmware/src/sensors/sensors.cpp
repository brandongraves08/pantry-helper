#include "sensors.h"

// GPIO pin assignments
const int DOOR_PIN = 33;      // Reed switch
const int LIGHT_PIN = 34;     // Analog light sensor
const int LIGHT_THRESHOLD = 100;

static unsigned long last_trigger_time = 0;
const unsigned long DEBOUNCE_MS = 2000;

void Sensors::init() {
    pinMode(DOOR_PIN, INPUT_PULLUP);
    pinMode(LIGHT_PIN, INPUT);
    Serial.println("[SENSORS] Initialized");
}

bool Sensors::check_door() {
    if (!digitalRead(DOOR_PIN)) {  // LOW = door open
        if (millis() - last_trigger_time > DEBOUNCE_MS) {
            last_trigger_time = millis();
            return true;
        }
    }
    return false;
}

bool Sensors::check_light() {
    int light_value = analogRead(LIGHT_PIN);
    if (light_value > LIGHT_THRESHOLD) {
        if (millis() - last_trigger_time > DEBOUNCE_MS) {
            last_trigger_time = millis();
            return true;
        }
    }
    return false;
}

void Sensors::debounce() {
    // Debounce logic integrated into individual checks
}
