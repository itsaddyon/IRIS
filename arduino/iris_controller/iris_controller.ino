/*
  IRIS Arduino Uno Controller
  ==========================
  Listens for severity commands from Python via serial (USB)
  and controls LEDs + buzzer accordingly.
  
  Serial Protocol:
    "LOW"    → Blue LED on, short low-tone beep
    "MEDIUM" → Yellow LED on, medium double-length beep
    "HIGH"   → Red LED on, one long high-tone beep
    "OFF"    → All off
  
  Pin Configuration:
    Pin 3 → Blue LED (Low severity)
    Pin 4 → Yellow LED (Medium severity)
    Pin 5 → Red LED (High severity)
    Pin 2 → Buzzer (All severities)
*/

// Pin definitions
#define PIN_BLUE_LED    3
#define PIN_YELLOW_LED  4
#define PIN_RED_LED     5
#define PIN_BUZZER      2

// Global variables
String commandBuffer = "";
boolean alert_active = false;
unsigned long alert_start_time = 0;
unsigned long alert_duration = 0;

const unsigned int LOW_BEEP_FREQ = 700;
const unsigned int MEDIUM_BEEP_FREQ = 1200;
const unsigned int HIGH_BEEP_FREQ = 2200;

const unsigned long LOW_BEEP_MS = 180;
const unsigned long MEDIUM_BEEP_MS = 450;
const unsigned long HIGH_BEEP_MS = 1200;

const unsigned long LOW_ALERT_MS = 700;
const unsigned long MEDIUM_ALERT_MS = 1000;
const unsigned long HIGH_ALERT_MS = 1500;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Configure pins as outputs
  pinMode(PIN_BLUE_LED, OUTPUT);
  pinMode(PIN_YELLOW_LED, OUTPUT);
  pinMode(PIN_RED_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  
  // Ensure all are off initially
  digitalWrite(PIN_BLUE_LED, LOW);
  digitalWrite(PIN_YELLOW_LED, LOW);
  digitalWrite(PIN_RED_LED, LOW);
  noTone(PIN_BUZZER);
  
  Serial.println("[IRIS] Arduino initialized");
  Serial.println("[IRIS] Awaiting commands: LOW, MEDIUM, HIGH, OFF");
}

void loop() {
  // Read serial input
  if (Serial.available() > 0) {
    char incomingChar = Serial.read();
    
    // Build command string until newline
    if (incomingChar == '\n') {
      processCommand(commandBuffer);
      commandBuffer = "";
    } else if (incomingChar != '\r') {
      commandBuffer += incomingChar;
    }
  }
  
  // Auto-off timeout for active alert
  if (alert_active) {
    unsigned long elapsedTime = millis() - alert_start_time;
    if (elapsedTime > alert_duration) {
      // Auto turn-off after timeout
      digitalWrite(PIN_BLUE_LED, LOW);
      digitalWrite(PIN_YELLOW_LED, LOW);
      digitalWrite(PIN_RED_LED, LOW);
      noTone(PIN_BUZZER);
      alert_active = false;
    }
  }
}

void processCommand(String command) {
  // Convert to uppercase for consistency
  command.toUpperCase();
  command.trim();
  
  if (command.length() == 0) {
    return;  // Ignore empty commands
  }
  
  // Reset timeout timer for any new command
  alert_start_time = millis();
  
  // Clear existing state — turn off ALL LEDs first
  digitalWrite(PIN_BLUE_LED, LOW);
  digitalWrite(PIN_YELLOW_LED, LOW);
  digitalWrite(PIN_RED_LED, LOW);
  noTone(PIN_BUZZER);
  alert_active = false;
  alert_duration = 0;
  
  // Process command
  if (command == "LOW") {
    Serial.println("[IRIS] LOW severity detected");
    digitalWrite(PIN_BLUE_LED, HIGH);   // ONLY Blue LED on
    tone(PIN_BUZZER, LOW_BEEP_FREQ, LOW_BEEP_MS);
    alert_active = true;
    alert_duration = LOW_ALERT_MS;
    
  } else if (command == "MEDIUM") {
    Serial.println("[IRIS] MEDIUM severity detected");
    digitalWrite(PIN_YELLOW_LED, HIGH);  // ONLY Yellow LED on
    tone(PIN_BUZZER, MEDIUM_BEEP_FREQ, MEDIUM_BEEP_MS);
    alert_active = true;
    alert_duration = MEDIUM_ALERT_MS;
    
  } else if (command == "HIGH") {
    Serial.println("[IRIS] HIGH severity detected");
    digitalWrite(PIN_RED_LED, HIGH);     // ONLY Red LED on
    tone(PIN_BUZZER, HIGH_BEEP_FREQ, HIGH_BEEP_MS);
    alert_active = true;
    alert_duration = HIGH_ALERT_MS;
    
  } else if (command == "OFF") {
    Serial.println("[IRIS] Alert OFF");
    // All already turned off above
    
  } else {
    Serial.print("[IRIS] Unknown command: ");
    Serial.println(command);
  }
}
