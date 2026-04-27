/*
  IRIS ESP8266 Wireless Controller
  ---------------------------------
  Connects to WiFi, listens for HTTP commands from IRIS laptop,
  triggers LEDs + buzzer accordingly.

  Setup:
  1. Install ESP8266 board in Arduino IDE:
     File > Preferences > Additional Boards Manager URLs:
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     Tools > Board Manager > search esp8266 > install
  2. Select Board: NodeMCU 1.0 (ESP-12E Module)
  3. Update WIFI_SSID and WIFI_PASS below
  4. Upload and open Serial Monitor (115200 baud)
  5. Note the IP address printed (e.g. 192.168.1.105)
  6. Update ARDUINO_IP in config.py with that IP

  Wiring:
    D5 (GPIO14) -> 220ohm -> Green LED  -> GND  [Low]
    D6 (GPIO12) -> 220ohm -> Orange LED -> GND  [Medium]
    D7 (GPIO13) -> 220ohm -> Red LED    -> GND  [High]
    D8 (GPIO15) -> Buzzer(+)            -> GND
*/

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASS = "YOUR_WIFI_PASS";

#define PIN_LOW   14
#define PIN_MED   12
#define PIN_HIGH  13
#define PIN_BUZZ  15

ESP8266WebServer server(80);

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LOW,  OUTPUT);
  pinMode(PIN_MED,  OUTPUT);
  pinMode(PIN_HIGH, OUTPUT);
  pinMode(PIN_BUZZ, OUTPUT);

  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());

  // Startup flash
  allOn(); delay(300); allOff();

  // HTTP routes
  server.on("/low",    handleLow);
  server.on("/medium", handleMedium);
  server.on("/high",   handleHigh);
  server.on("/ping",   handlePing);
  server.begin();
  Serial.println("IRIS ESP8266 ready!");
}

void loop() {
  server.handleClient();
}

void handleLow() {
  playPattern(PIN_LOW, 700, 160, 1, 0);
  server.send(200, "text/plain", "OK_LOW");
}

void handleMedium() {
  playPattern(PIN_MED, 1200, 180, 2, 120);
  server.send(200, "text/plain", "OK_MEDIUM");
}

void handleHigh() {
  playPattern(PIN_HIGH, 2200, 950, 1, 0);
  server.send(200, "text/plain", "OK_HIGH");
}

void handlePing() {
  server.send(200, "text/plain", "PONG");
}

void allOn() {
  digitalWrite(PIN_LOW, HIGH);
  digitalWrite(PIN_MED, HIGH);
  digitalWrite(PIN_HIGH, HIGH);
}

void allOff() {
  digitalWrite(PIN_LOW, LOW);
  digitalWrite(PIN_MED, LOW);
  digitalWrite(PIN_HIGH, LOW);
  noTone(PIN_BUZZ);
}

void playPattern(int ledPin, int toneHz, int toneMs, int repeats, int gapMs) {
  allOff();

  for (int i = 0; i < repeats; i++) {
    digitalWrite(ledPin, HIGH);
    tone(PIN_BUZZ, toneHz, toneMs);
    delay(toneMs);
    noTone(PIN_BUZZ);
    digitalWrite(ledPin, LOW);

    if (i < repeats - 1 && gapMs > 0) {
      delay(gapMs);
    }
  }

  allOff();
}
