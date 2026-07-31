#ifndef TELNET_H
#define TELNET_H

#include <Arduino.h>

class TelnetServer {
public:
    static void init();
    static void handle();
    static void println(const String& message);
    static void print(const String& message);
    
private:
    static const uint16_t PORT = 23;
};

#endif
