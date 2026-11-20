// FSR solo test for a bare ESP32: FSR between 3V3 and D32, nothing else.
// The pin's built-in pull-down stands in for the 10 kOhm resistor. analogRead() turns the normal
// pull-down off, so it is re-enabled through the RTC IO block (which the ADC keeps) every loop.
#include "driver/rtc_io.h"
void setup() {
  Serial.begin(115200);
  analogSetPinAttenuation(32, ADC_11db);
}
void loop() {
  pinMode(32, INPUT_PULLDOWN);              // digital: pressed = 1
  delay(2);
  int d = digitalRead(32);
  int v = analogRead(32);                   // analog: 0 at rest, high when pressed
  rtc_gpio_pullup_dis(GPIO_NUM_32);
  rtc_gpio_pulldown_en(GPIO_NUM_32);
  Serial.printf("FSR %d D %d\n", v, d);
  delay(50);
}
