// WristTap firmware v2 (ESP32): 2x MPU6050 + 4 piezo + 2 FSR.
// Streams the SAME 44-byte packet three ways at once:
//   USB serial   921600 baud, 500 packets/s (as before)
//   Wi-Fi UDP    port 4210, 10 packets per datagram (500 packets/s), broadcast on the local network
//   Bluetooth LE device "WristTap", 100 packets/s in notifications of 4 (piezo peaks kept over each 10 ms)
// No extra libraries needed (WiFi + BLE come with the ESP32 Arduino core).
//
// Wi-Fi: put your network in secrets.h (copy secrets.example.h). With no secrets.h, or if the
// network isn't found in 8 s, the band makes its OWN network: "WristTap", password "wristtap1".
// Join it from the Mac (the Mac then has no internet while joined).
//
// Wiring (unchanged)
//   MPU6050 #1 (forearm box):  VCC->3V3, GND->GND, SDA->GPIO21, SCL->GPIO22, AD0->GND   (0x68)
//   MPU6050 #2 (back of hand): same 4 wires, but AD0->3V3                              (0x69)
//   Piezo n: red -> 10k -> GPIO, black -> GND, 1M from GPIO to GND. pins 32, 33, 34, 35
//   FSR n:   one leg -> 3V3, other leg -> GPIO + 10k to GND. pins 36 (VP), 39 (VN)
//
// Packet (little-endian, 44 bytes):
//   uint16 0x55AA | uint32 micros | int16 imu1[6] | int16 imu2[6] | uint16 piezoPeak[4] | uint16 fsr[2] | uint16 seq
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>

#if __has_include("secrets.h")
#include "secrets.h"
#else
#define WIFI_SSID ""
#define WIFI_PASS ""
#endif

const int PIEZO[4] = {32, 33, 34, 35};
const int FSR[2] = {36, 39};
const uint8_t IMU_ADDR[2] = {0x68, 0x69};
bool imuOk[2] = {false, false};

const uint32_t PERIOD_US = 2000;   // 500 Hz packets
const int PKT = 44;
uint16_t seq = 0;

// ── Wi-Fi ───────────────────────────────────────────────────
const uint16_t UDP_PORT = 4210;
const int UDP_BATCH = 10;
WiFiUDP udp;
IPAddress bcast;
bool wifiUp = false;
uint8_t udpBuf[PKT * UDP_BATCH];
int udpN = 0;

// ── BLE (UUIDs are WristTap's own) ──────────────────────────
#define BLE_SERVICE "7a1e0001-5752-4954-5441-500000000001"
#define BLE_DATA    "7a1e0002-5752-4954-5441-500000000001"
BLECharacteristic *bleData = nullptr;
volatile bool bleConnected = false;
uint16_t bleSeq = 0;
uint16_t blePeak[4] = {0, 0, 0, 0};
int bleCount = 0;
const int BLE_BATCH = 4;            // the Mac takes ~1 notification per 30-40 ms, so send 4 packets in each
uint8_t bleBuf[PKT * BLE_BATCH];
int bleN = 0;

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer *s) override { bleConnected = true; }
  void onDisconnect(BLEServer *s) override { bleConnected = false; BLEDevice::startAdvertising(); }
};

bool imuWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

bool imuInit(uint8_t addr) {
  if (!imuWrite(addr, 0x6B, 0x01)) return false;  // wake, PLL with gyro X clock
  imuWrite(addr, 0x1A, 0x00);   // DLPF off: accel 260 Hz bandwidth (keeps sharp tap edges)
  imuWrite(addr, 0x19, 0x00);   // sample rate divider 0
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
  // An MPU that lost power still answers but reads all zeros (it fell back asleep):
  // report it missing so the retry below wakes it up again.
  bool allZero = true;
  for (int i = 0; i < 6; i++) if (out[i]) allZero = false;
  return !allZero;
}

void startWifi() {
  if (strlen(WIFI_SSID) > 0) {
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);              // no power-save naps: steady 500 Hz
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 8000) delay(100);
  }
  if (WiFi.status() == WL_CONNECTED) {
    IPAddress ip = WiFi.localIP(), m = WiFi.subnetMask();
    bcast = IPAddress(ip[0] | ~m[0], ip[1] | ~m[1], ip[2] | ~m[2], ip[3] | ~m[3]);
  } else {
    WiFi.disconnect(true);
    WiFi.mode(WIFI_AP);
    WiFi.softAP("WristTap", "wristtap1");
    WiFi.setSleep(false);
    bcast = IPAddress(192, 168, 4, 255);
  }
  udp.begin(UDP_PORT);
  wifiUp = true;
}

void startBle() {
  BLEDevice::init("WristTap");
  BLEDevice::setMTU(185);           // room for 4 packets (176 bytes) per notification
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCB());
  BLEService *svc = server->createService(BLE_SERVICE);
  bleData = svc->createCharacteristic(BLE_DATA, BLECharacteristic::PROPERTY_NOTIFY);
  bleData->addDescriptor(new BLE2902());
  svc->start();
  BLEAdvertising *adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(BLE_SERVICE);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void setup() {
  Serial.begin(921600);
  Wire.begin(21, 22);
  Wire.setClock(400000);
  analogReadResolution(12);
  for (int i = 0; i < 4; i++) analogSetPinAttenuation(PIEZO[i], ADC_0db);   // most sensitive range for small piezo signals
  for (int i = 0; i < 2; i++) analogSetPinAttenuation(FSR[i], ADC_11db);   // full 0-3.3 V for the FSR divider
  for (int i = 0; i < 2; i++) imuOk[i] = imuInit(IMU_ADDR[i]);
  startBle();
  startWifi();
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

  uint8_t pkt[PKT];
  uint16_t magic = 0x55AA;
  uint32_t t = micros();
  int16_t imu[2][6];
  for (int k = 0; k < 2; k++) {
    if (imuOk[k]) imuOk[k] = imuRead(IMU_ADDR[k], imu[k]); else memset(imu[k], 0, 12);
  }
  // No-solder sensors can lose contact: keep retrying a missing one twice a second.
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

  // 1) USB (only when a Mac is listening on the cable; skipped on battery so it never blocks)
  if (Serial.availableForWrite() >= PKT) Serial.write(pkt, PKT);

  // 2) Wi-Fi: 10 packets per datagram = 50 datagrams/s
  if (wifiUp) {
    memcpy(udpBuf + udpN * PKT, pkt, PKT);
    if (++udpN == UDP_BATCH) {
      udp.beginPacket(bcast, UDP_PORT);
      udp.write(udpBuf, sizeof(udpBuf));
      udp.endPacket();
      udpN = 0;
    }
  }

  // 3) Bluetooth: every 5th packet, carrying the max piezo peak of those 5 and its own seq
  for (int i = 0; i < 4; i++) if (peak[i] > blePeak[i]) blePeak[i] = peak[i];
  if (++bleCount == 5) {
    bleCount = 0;
    if (bleConnected) {
      uint8_t *b = bleBuf + bleN * PKT;
      memcpy(b, pkt, PKT);
      memcpy(b + 30, blePeak, 8);
      memcpy(b + 42, &bleSeq, 2);
      bleSeq++;
      if (++bleN == BLE_BATCH) {
        bleData->setValue(bleBuf, sizeof(bleBuf));
        bleData->notify();
        bleN = 0;
      }
    } else bleN = 0;
    memset(blePeak, 0, sizeof(blePeak));
  }

  // Fell far behind (e.g. radio busy): resync instead of bursting.
  if ((int32_t)(micros() - next) > 20000) next = micros() + PERIOD_US;
}
