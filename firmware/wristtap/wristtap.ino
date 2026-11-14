// WristTap firmware (ESP32): 2x MPU6050 + 4 piezo + 2 FSR, streamed over USB serial.
// No extra libraries needed (raw I2C).
//
// Wiring
//   MPU6050 #1 (wrist):      VCC->3V3, GND->GND, SDA->GPIO21, SCL->GPIO22, AD0->GND   (address 0x68)
//   MPU6050 #2 (back of hand): same 4 wires, but AD0->3V3                             (address 0x69)
//   Piezo n:  red wire -> 10 kOhm resistor -> GPIO pin (protects the pin), black wire -> GND,
//             and a 1 MOhm resistor from the GPIO pin to GND (drains charge)
//             pins: piezo0=32, piezo1=33, piezo2=34, piezo3=35
//   FSR n:    one leg -> 3V3, other leg -> GPIO pin, and a 10 kOhm resistor from that pin to GND
//             pins: fsr0=36 (VP), fsr1=39 (VN)
//   Missing sensors are fine: their values just read 0, and the firmware retries them every 0.5 s.
//
// Packet (little-endian, 44 bytes, 500 per second):
//   uint16 0x55AA | uint32 micros | int16 imu1[6] | int16 imu2[6] | uint16 piezoPeak[4] | uint16 fsr[2] | uint16 seq
#include <Wire.h>

const int PIEZO[4] = {32, 33, 34, 35};
const int FSR[2] = {36, 39};
const uint8_t IMU_ADDR[2] = {0x68, 0x69};
bool imuOk[2] = {false, false};

const uint32_t PERIOD_US = 2000;   // 500 Hz packets
uint16_t seq = 0;

bool imuWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

bool imuInit(uint8_t addr) {
  if (!imuWrite(addr, 0x6B, 0x01)) return false;  // wake, PLL with gyro X clock
  imuWrite(addr, 0x1A, 0x00);   // DLPF off: accel 260 Hz bandwidth (keeps sharp tap edges)
  imuWrite(addr, 0x19, 0x00);   // sample rate divider 0 -> 8 kHz gyro / 1 kHz accel
  imuWrite(addr, 0x1B, 0x10);   // gyro +-1000 dps
  imuWrite(addr, 0x1C, 0x10);   // accel +-8 g
  return true;
}

bool imuRead(uint8_t addr, int16_t *out) {
  Wire.beginTransmission(addr);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) { memset(out, 0, 12); return false; }
  if (Wire.requestFrom((int)addr, 14) != 14) { memset(out, 0, 12); return false; }
  uint8_t b[14];
  for (int i = 0; i < 14; i++) b[i] = Wire.available() ? Wire.read() : 0;
  out[0] = (b[0] << 8) | b[1];   // ax
  out[1] = (b[2] << 8) | b[3];   // ay
  out[2] = (b[4] << 8) | b[5];   // az
  out[3] = (b[8] << 8) | b[9];   // gx  (b[6..7] is temperature)
  out[4] = (b[10] << 8) | b[11]; // gy
  out[5] = (b[12] << 8) | b[13]; // gz
  return true;
}

void setup() {
  Serial.begin(921600);
  Wire.begin(21, 22);
  Wire.setClock(400000);
  analogReadResolution(12);
  for (int i = 0; i < 4; i++) analogSetPinAttenuation(PIEZO[i], ADC_0db);   // most sensitive range for small piezo signals
  for (int i = 0; i < 2; i++) analogSetPinAttenuation(FSR[i], ADC_11db);   // full 0-3.3 V for the FSR divider
  for (int i = 0; i < 2; i++) imuOk[i] = imuInit(IMU_ADDR[i]);
}

void loop() {
  static uint32_t next = micros();
  uint16_t peak[4] = {0, 0, 0, 0};

  // Between packets, sample the piezos as fast as possible and keep each one's peak,
  // so a short tap spike is not missed by the 500 Hz packet rate.
  while ((int32_t)(micros() - next) < 0) {
    for (int i = 0; i < 4; i++) {
      uint16_t v = analogRead(PIEZO[i]);
      if (v > peak[i]) peak[i] = v;
    }
  }
  next += PERIOD_US;

  uint8_t pkt[44];
  uint16_t magic = 0x55AA;
  uint32_t t = micros();
  int16_t imu[2][6];
  for (int k = 0; k < 2; k++) {
    if (imuOk[k]) imuOk[k] = imuRead(IMU_ADDR[k], imu[k]); else memset(imu[k], 0, 12);
  }
  // No-solder (press-fit) sensors can lose contact: keep retrying a missing one twice a second.
  static uint32_t lastRetry = 0;
  if (millis() - lastRetry > 500) {
    lastRetry = millis();
    for (int k = 0; k < 2; k++) if (!imuOk[k]) imuOk[k] = imuInit(IMU_ADDR[k]);
  }
  uint16_t fsr[2] = {(uint16_t)analogRead(FSR[0]), (uint16_t)analogRead(FSR[1])};

  int o = 0;
  memcpy(pkt + o, &magic, 2); o += 2;
  memcpy(pkt + o, &t, 4); o += 4;
  memcpy(pkt + o, imu[0], 12); o += 12;
  memcpy(pkt + o, imu[1], 12); o += 12;
  memcpy(pkt + o, peak, 8); o += 8;
  memcpy(pkt + o, fsr, 4); o += 4;
  memcpy(pkt + o, &seq, 2); o += 2;
  seq++;
  Serial.write(pkt, 44);

  // Fell far behind (e.g. USB stall): resync instead of bursting.
  if ((int32_t)(micros() - next) > 20000) next = micros() + PERIOD_US;
}
