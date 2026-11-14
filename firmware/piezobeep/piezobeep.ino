// WristTap disc beep test: plays a 3 kHz beep on D32 (0.3 s on, 0.7 s off).
// Disc red wire must be on D32's row (g9), black on GND. Run ./flash.sh after to restore WristTap.
const int PIN = 32;
void setup() { Serial.begin(115200); }
void loop() {
  tone(PIN, 3000);  delay(300);
  noTone(PIN);      delay(700);
  Serial.println("beep");
}
