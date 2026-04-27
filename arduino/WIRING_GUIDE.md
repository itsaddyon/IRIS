# IRIS Arduino Wiring Guide
# For Suraj — RC Car Hardware Setup

## Components (from Robu.in order)
- Arduino Uno R3
- Breadboard MB102 830 points
- 1x Red LED (10mm DIP)
- 1x Yellow LED (10mm DIP)
- 1x Blue LED (10mm DIP)
- 10x 220Ω Resistors
- Active Buzzer (5V)
- Male-Male Jumper Wires
- Male-Female Jumper Wires
- USB cable (comes with Arduino)

## Wiring

Arduino Pin 8  → 220Ω resistor → Blue LED(+)   → GND   [Low severity]
Arduino Pin 9  → 220Ω resistor → Yellow LED(+) → GND   [Medium severity]
Arduino Pin 10 → 220Ω resistor → Red LED(+)    → GND   [High severity]
Arduino Pin 11 → Buzzer (+)                    → GND   [All severities]
Arduino GND    → Breadboard GND rail

## RC Car Setup

1. Open RC car body — enough space for Arduino + breadboard
2. Mount breadboard inside car with double-sided tape
3. Place Arduino next to breadboard
4. Route USB cable out from back of car to laptop
5. Mount phone on TOP of car pointing straight down at road
6. Secure phone with double-sided tape or rubber band

## Phone Camera Height
- Phone should be 10-15cm above road surface
- Point straight down at road
- Make sure full road width is in frame
- Open IP Webcam app before starting IRIS

## Software Setup

1. Upload iris_controller.ino to Arduino:
   - Open Arduino IDE
   - File > Open > D:\Btech Projects\IRIS\arduino\iris_controller\iris_controller.ino
   - Tools > Board > Arduino Uno
   - Tools > Port > (select COM port from Device Manager)
   - Click Upload

2. Update config.py:
   - ARDUINO_MODE = 'serial'
   - ARDUINO_ENABLED = True
   - ARDUINO_PORT = 'COM3'  (check Device Manager for correct port)

3. Test:
   - Run: python main.py
   - All 3 LEDs flash once on startup = IRIS_READY

## Demo Flow
1. Place RC car at start of road model
2. Login to IRIS dashboard → select vehicle → Start Inspection
3. Drive RC car slowly using remote over road model
4. Pothole detected:
   - Low    → Blue LED blinks
   - Medium → Yellow LED + 2 short buzzes
   - High   → Red LED flashes 4x + loud buzz + snapshot saved
5. End session → data uploads to Municipal Dashboard
