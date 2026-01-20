// Minimal test - compile this instead to test serial
#include <Arduino.h>

void setup() {
    delay(500);
    Serial.begin(115200);
    delay(100);
    
    for (int i = 0; i < 10; i++) {
        Serial.print("Hello ");
        Serial.println(i);
        delay(100);
    }
}

void loop() {
    Serial.println("Loop tick");
    delay(1000);
}
