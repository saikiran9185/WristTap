// WristTap I2C test: checks each MPU wire separately, then scans the bus.
// Prints a report every 2 s at 115200 baud. Flash the real firmware back with ./flash.sh after.
#include <Wire.h>

// Wire test: ESP32 pulls the pin weakly LOW. The GY-521 board has its own pull-up
// resistors on SDA/SCL, so if the wire really reaches the MPU, the pin reads HIGH.
const char* wireCheck(int pin) {
  pinMode(pin, INPUT_PULLDOWN);
  delay(5);
  return digitalRead(pin) ? "CONNECTED to MPU" : "NOT connected (no MPU pull-up seen)";
}

void scan(int sda, int scl, const char* label) {
  Wire.begin(sda, scl, 100000);
  int found = 0;
  Serial.printf("  Scan with SDA=D%d SCL=D%d %s: ", sda, scl, label);
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      found++;
      Wire.beginTransmission(a); Wire.write(0x75); Wire.endTransmission(false);
      Wire.requestFrom((int)a, 1);
      int id = Wire.available() ? Wire.read() : -1;
      Serial.printf("0x%02X (chip id 0x%02X)  ", a, id);
    }
  }
  if (!found) Serial.print("nothing answered");
  Serial.println();
  Wire.end();
}

void setup() { Serial.begin(115200); delay(500); }

void loop() {
  Serial.println("---- WristTap I2C test ----");
  Serial.printf("  D21 (blue, SDA)  : %s\n", wireCheck(21));
  Serial.printf("  D22 (yellow, SCL): %s\n", wireCheck(22));
  scan(21, 22, "(correct)");
  scan(22, 21, "(swapped)");
  delay(2000);
}
