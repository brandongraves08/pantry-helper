#ifndef WEBSERVER_H
#define WEBSERVER_H

#include <Arduino.h>
#include <vector>

class WebServer {
public:
    static void init();
    static void handle();
    static void add_log(const String& message);
    static String get_status_json();
    
private:
    static std::vector<String> logs;
    static const int MAX_LOGS = 50;
};

#endif
