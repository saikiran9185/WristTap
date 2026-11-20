# IMU Hardware Options That Reduce Drift (ESP32 wristband + upper-arm band)

Research date: 15 Nov 2026. Prices are approximate and were taken from search snippets and cached pages on this date. Check them live before buying.

## Q1. Sensor comparison: noise, drift, fusion, interfaces

### Takeaway
The current MPU6050/MPU6500 is the worst choice for yaw drift. SlimeVR's community testing (the closest real-world analogue: body-worn ESP32 trackers estimating limb orientation) puts the MPU6500 at about 5-10 minutes before a heading reset is needed. The ICM-45686 and LSM6DSV are at about 45-60 minutes, and the BNO085 is also at about 45-60 minutes. For a new 2026 design, the best value is an ICM-45686 or LSM6DSV16X with host-side fusion, or with the LSM6DSV16X's on-chip SFLP quaternion. The BNO085/086 is the easiest "fusion in a box" option, but it costs more, is listed as discontinued by SlimeVR, and has ESP32 I2C quirks.

### Cited Findings

**Real-world drift ranking from body-worn trackers (SlimeVR, ESP-based, 6DOF yaw drift, "reset time")**
- Ranked best to worst with current firmware. Times are typical minutes before a reset:
  - Superior: ICM-45686, about $6.70, 45-60 min, "Best currently available", 6DOF with no magnetometer. LSM6DSV, about $5.80, 45-50 min, "a bit less temperature stable than ICM45686 on paper".
  - Affordable: LSM6DSR, about $3.35, 25-30 min.
  - Legacy: LSM6DSO, 25-35 min, no reliable breakout seller.
  - Poor: BNO085, 45-60 min, but "discontinued", "suffers significantly from the stomp bug", and listings are "Very misleading". BMI270, 10-20 min. ICM-42688, about $8, 25-30 min, "temperature sensitive and drifts fairly quickly". ICM-20948, about $15, 15-60 min, drifts on very fast motion in 6DOF and is "Sensitive to bad magnetic environments". BNO055, about $38, 1-10 min, "High drift rate", needs calibration on each start.
  - Avoid: BMI160, MPU9250, MPU+QMC5883L, MPU6500 (about $1, 5-10 min, "High drift rate", calibration on each start) and MPU6050 (about $1.04, 1-5 min, "loses accuracy within minutes", "High failure rate").
  - [SlimeVR IMU Comparison](https://docs.slimevr.dev/diy/imu-comparison.html)
- Reddit anecdotes give similar drift times: LSM6DSV about 40-50 min and BNO085 about 30-60 min. One BNO085 user says it "drifts less than BMIs by a lot" but has the stomping bug — [SlimeVR IMU Comparison search summary / r/SlimeVR thread](https://redlib.belloworld.it/r/SlimeVR/comments/1fw3cgd/whats_the_difference_between_icm42688_and_bno085)
- SlimeVR's firmware support for the LSM6DSV was marked experimental at one point — [SlimeVR Tracker ESP fork](https://github.com/sojifes/SlimeVR-Tracker-ESP) (via search summary; check the current upstream status)

**Datasheet-level specs**

| Part | Gyro noise density | Accel noise | Bias instability / temperature | Max ODR | Interfaces | On-chip fusion | Mag |
|---|---|---|---|---|---|---|---|
| ICM-45686 (TDK) | 3.8 mdps/√Hz | 70 µg/√Hz | Claimed "highest stability against temperature, shock, SMT/bend-induced offset"; no number given | up to 6.4 kHz | I3C 12.9 MHz / I2C 1 MHz / SPI 24 MHz; AUX I2C master | No (8 KB FIFO) | No (AUX port can host one) |
| ICM-42688-P (TDK) | 2.8 mdps/√Hz | 65-70 µg/√Hz | SlimeVR calls it "temperature sensitive" | 32 kHz | I2C/SPI | No (2 KB FIFO) | No |
| BMI270 (Bosch) | 0.007 dps/√Hz performance mode; 0.010 normal mode (25 °C) | "higher" | — | 6.4 kHz | I2C/SPI | No (gesture features only) | No |
| BMI088 (Bosch) | 0.014 °/s/√Hz | 230 µg/√Hz | Flyer: <2 °/h (1σ typical). Not in the datasheet. User test of 57 sensors averaged about 3.2 °/h on X/Y | — | I2C/SPI | No | No |
| LSM6DSV16X (ST) | about 3.8 mdps/√Hz (secondary source, not confirmed in ST's PDF) | — | SlimeVR: slightly less temperature-stable than the ICM-45686 | — | I2C/SPI/I3C | Yes: SFLP 6-axis game rotation vector quaternion into FIFO | No (SlimeVR boards pair it with a QMC6309) |
| ICM-20948 (TDK) | 0.015 dps/√Hz (TDK table; unit label garbled) | — | — | — | I2C/SPI | DMP | Yes (AK09916) |
| BNO085/086 (CEVA) | n/a (fused output) | — | Game RV 0.5°/min heading drift; dynamic error 2.5°, static 1.5° | — | I2C 400 kHz, SPI 3 MHz, UART 3 Mbps | Yes (SH-2 on Cortex-M0) | Yes |

Sources for the table:
- ICM-45686: 3.8 mdps/√Hz, 70 µg/√Hz, ODR up to 6.4 kHz, I3C/I2C 1 MHz/SPI 24 MHz, 8 KB FIFO, 0.42 mA 6-axis low-noise mode, about $5.86 at DigiKey in mid-2026. The page warns that third-party listings quoting a "256-byte FIFO" and ">±3 °/s zero-rate offset" are wrong, and points to TDK DS-000577 — [pcbsync ICM-45686](https://pcbsync.com/icm-45686/)
- ICM-42688-P vs ICM-45686 vs BMI270 comparison: 2.8 vs 3.8 vs about 7 mdps/√Hz; FSR ±2000 vs ±4000 dps; 32 kHz vs 6.4 kHz ODR; 0.88 mA vs 0.42 mA; about $4.67 vs $5.86 single quantity — [pcbsync ICM-45686](https://pcbsync.com/icm-45686/). This is a secondary, commercial site, so verify against the TDK datasheets.
- BMI270: 0.007 dps/√Hz performance mode and 0.010 normal — [Bosch BMI270 datasheet (SparkFun copy)](https://cdn.sparkfun.com/assets/9/a/2/9/6/bst-bmi270-ds000.pdf); [Bosch BMI270 product page](https://bosch-sensortec.com/products/motion-sensors/imus/bmi270.html), which reportedly lists 0.008 dps/√Hz in its table, a small conflict between Bosch sources
- BMI088: 0.014 °/s/√Hz gyro, 230 µg/√Hz accel, bias stability <2 °/h — [Bosch BMI088 flyer](https://www.bosch-sensortec.com/media/boschsensortec/downloads/product_flyer/bst-bmi088-fl000.pdf). The bias instability is not in the datasheet and the 2 °/h figure is 1σ typical — [Bosch community](https://community.bosch-sensortec.com/t5/MEMS-sensors-forum/BMI088-Bias-Instability-and-Alignment-errors-not-specified-in/m-p/12037). A user measured 57 axes: only 11 were below 2 °/h, and the X/Y average was about 3.2 °/h — [Bosch community](https://community.bosch-sensortec.com/t5/MEMS-sensors-forum/BMI088-bias-instability-more-than-4deg-hr/m-p/92620)
- LSM6DSV16X: embedded "sensor fusion low-power (SFLP) algorithm able to provide a 6-axis game rotation vector represented as a quaternion" stored in FIFO; Qvar electrostatic sensing for tap, double/triple tap, long press and L/R swipe; gyro FS ±125 to ±4000 dps; 0.65 mA combo high-performance mode — [LSM6DSV16X datasheet (SparkFun copy)](https://cdn.sparkfun.com/assets/4/1/8/e/2/lsm6dsv16x.pdf); [ST AN5763](https://cdn.sparkfun.com/assets/0/a/c/c/9/an5763-lsm6dsv16x-6axis-imu-with-embedded-sensor-fusion-ai-qvar-for-highend-applications-stmicroelectronics.pdf); [ST product page](https://www.st.com/en/mems-and-sensors/lsm6dsv16x.html). The 3.8 mdps/√Hz noise figure comes only from secondary comparisons — [pcbsync ICM-42688-P](https://pcbsync.com/icm-42688-p/)
- An ST forum user reported LSM6DSV16X SFLP drift of "upwards of 20 degrees over 5 minutes". This is an anecdote and likely reflects their configuration or calibration — [ST community: LSM6DSV16X drift issue](https://community.st.com/mems-sensors-48/lsm6dsv16x-drift-issue-119441)
- ICM-20948: 0.015 gyro noise in a TDK comparison table — [TDK InvenSense](https://invensense.tdk.com/?p=6841)
- BNO086: Rotation Vector dynamic error 3.5° / static 2.0°; Game RV 2.5° / 1.5° with 0.5°/min heading drift; Geomagnetic RV 4.5° / 3.0°; gravity angle 1.5°; I2C up to 400 kHz, SPI up to 3 MHz, UART 3 Mbps — [SparkFun BNO086 product page](https://www.sparkfun.com/products/retired/14686)
- BNO085 uses "the same hardware as the BNO055 but very different firmware", running SH-2 on a Cortex-M0. It offers rotation vectors, calibrated/uncalibrated/raw outputs, stability detection and classification, tap/step/shake detection, and a UART-RVC mode — [Adafruit BNO085 guide](https://learn.adafruit.com/adafruit-9-dof-orientation-imu-fusion-breakout-bno085?view=all)

**Higher-grade references (out of hobby budget; shown for scale)**
- Murata SCH16T-K20: bias instability 0.3-0.5 °/h; ARW about 0.015-0.019 °/√h (XY) and 0.025-0.028 °/√h (Z) — [Murata SCH16T-K20 short datasheet](https://www.sensor-test.de/assets/Fairs/2026/ProductNews/PDFs/SCH16T-K20-short_1640-21648-0033-E-0126.pdf); [Future Electronics](https://www.futureelectronics.com/resources/featured-products/murata-sch16t-series-combined-gyro-sensor-and-accelerometer)
- Epson M-G370: gyro bias instability 0.8 °/h; ARW 0.06 °/√h (0.03 °/√h on PDS0/PDT0 variants) — [Epson M-G370](https://global.epson.com/products_and_drivers/sensing_system/imu/g370); [M-G370PDT0 brief](https://global-origin.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g370pdt0_briefsheet_e.pdf)

### Inferences
- Unit conversion for comparison: 0.007 dps/√Hz = 7 mdps/√Hz. On noise density alone, the ranking is ICM-42688-P (2.8) < ICM-45686 ≈ LSM6DSV16X (about 3.8) < BMI270 (7) < BMI088 (14) ≈ ICM-20948 (about 15). Real-world drift does not follow noise density: the ICM-42688-P has the best noise figure but only mid-pack drift times. Yaw drift is dominated by bias stability over temperature and by the fusion and calibration firmware, not by white noise.
- The Murata and Epson parts are about 10x better in bias instability than the BMI088's 2-3 °/h. Even 2 °/h is about 0.03°/min, far below what the hobby parts achieve in practice. The 0.5°/min BNO game RV spec is therefore dominated by uncompensated bias and temperature behaviour, not the sensor noise floor.
- The upper arm and wrist do not need a magnetometer if drift is handled by host-side corrections, such as zero-velocity or still detection to re-estimate gyro bias, plus kinematic constraints between the two IMUs. The ICM-45686 or LSM6DSV16X are the best value for that approach.
- The LSM6DSV16X's Qvar could double as a capacitive "tap/touch" input on the wristband, which fits the WristTap concept. That is a design opportunity, not a tested claim.

### Gaps
- No primary-datasheet gyro noise figure for the MPU6500, MPU6050 or BNO055 was retrieved in this session. The TDK MPU-6500 datasheet should be checked directly.
- ICM-45686 and LSM6DSV16X gyro noise and temperature-offset numbers were not confirmed from the TDK DS-000577 or ST datasheet PDFs (secondary sources only).
- LSM6DSO and LSM6DSOX datasheet noise figures were not retrieved.
- No controlled, lab-grade head-to-head drift benchmark of the ICM-45686 vs LSM6DSV vs BNO085 was found; SlimeVR's times are community estimates.
- ADIS16470 specs and prices for all high-grade parts were not found.

## Q2. BNO085 real-world heading drift: game rotation vector vs rotation vector, magnetic disturbance

### Takeaway
The only published number is about 0.5°/min heading drift for the BNO086 game rotation vector (gyro + accel, no magnetometer). That is roughly 30° per hour in the worst case, though SlimeVR users typically get 45-60 minutes before a reset. The magnetometer-based rotation vector removes long-term drift, but it is less accurate dynamically (3.5° vs 2.5°) and suffers indoors. The Adafruit library deliberately avoids magnetometer correction in the game quaternion to avoid sudden heading jumps.

### Cited Findings
- Game Rotation Vector: dynamic heading drift 0.5°/min, dynamic error 2.5°, static error 1.5°. Rotation Vector (with magnetometer): dynamic error 3.5°, static 2.0°. Geomagnetic RV: 4.5° / 3.0° — [SparkFun BNO086](https://www.sparkfun.com/products/retired/14686). This is a retailer copy of the CEVA spec.
- The game quaternion "is not corrected using the magnetometer", to avoid sudden heading jumps, so slow drift is expected — [Adafruit CircuitPython BNO08x API](https://docs.circuitpython.org/projects/bno08x/en/latest/api.html)
- The full rotation vector uses accel + gyro + mag for absolute orientation. The geomagnetic RV uses mag + accel only, with no gyro. A guide states the hub "can compensate for interference with the magnetic field, e.g. from magnets, loudspeakers or ferromagnetic materials" — [Wolles Elektronikkiste: BNO08x](https://wolles-elektronikkiste.de/en/bno08x-9-dof-imus)
- The stability classifier reports states such as "On Table" (at rest, very little vibration) and "Unknown" — [Adafruit CircuitPython BNO08x API](https://docs.circuitpython.org/projects/bno08x/en/latest/api.html). CEVA has a calibration procedure document (dynamic calibration of accel/gyro/mag) — [CEVA BNO080/BNO085 Sensor Calibration Procedure](https://xdevs.com/doc/CEVA/BNO080-BNO085-Sesnor-Calibration-Procedure.pdf)
- Users report inaccurate heading with the 9-axis rotation vector indoors and calibration difficulty — [SparkFun community: Inaccurate heading with BNO085](https://community.sparkfun.com/t/inaccurate-heading-and-calibration-issues-with-bno085-imu/47544); [Arduino forum: BNO085 calibration process](https://forum.arduino.cc/t/bno085-calibration-process/904696)
- One user found the game RV better than 9-DOF indoors but still saw periodic drift. Another saw the quaternion shift slowly under constant low-amplitude vibration — [SparkFun community: BNO086 readings](https://community.sparkfun.com/t/bno086-explanation-and-detailed-info-for-readings-please/66713) (via search summary)
- The analogous Bosch BHI260AB game RV also drifts in yaw over time without a magnetometer — [Bosch community: BHI260AB GRV drift](https://community.bosch-sensortec.com/t5/MEMS-sensors-forum/BHI260AB-Game-Rotation-Vector-drift-over-time/m-p/52014)
- SlimeVR: magnetometers need a stable magnetic environment; interference does not itself cause drift but can force resets; the ICM-20948 is "sensitive to bad magnetic environments" — [SlimeVR IMU Comparison](https://docs.slimevr.dev/diy/imu-comparison.html)
- BNO085 "stomp bug": SlimeVR reports significant tracking errors after sharp impacts — [SlimeVR IMU Comparison](https://docs.slimevr.dev/diy/imu-comparison.html)

### Inferences
- At 0.5°/min, a 10-minute demo could accumulate up to about 5° of yaw error per IMU. Two IMUs drifting independently will also distort the computed elbow and hand position. For a wristband plus upper-arm band, use the game RV and correct relative yaw between the two segments with kinematic constraints, such as the elbow hinge, rather than trusting the magnetometer indoors (steel desks, laptops, speakers).
- Wrist-worn sensors sit near phones, laptops and watches, so magnetometer use on the wrist is especially risky. The near-wrist magnetic environment is likely worse than the upper arm's.

### Gaps
- No independent, controlled deg/min measurement of the BNO085 RV vs GRV was found; the 0.5°/min figure is a spec value.
- The CEVA datasheet's exact wording on magnetic disturbance rejection was not read directly.

## Q3. ESP32 integration: libraries, I2C addresses, multiple IMUs, sample rates, time sync

### Takeaway
BNO08x parts use non-standard I2C clock stretching that misbehaves on ESP32. Use SPI (PS1 strap) or UART-RVC for reliability. Raw IMUs (ICM-45686, LSM6DSV16X, ICM-42688) are simpler: two units can share one I2C bus via different addresses, or each can get its own SPI chip-select. Hardware FIFOs plus a shared timestamp from the ESP32 make sync easy.

### Cited Findings
- BNO080/085/086 use non-standard I2C clock stretching, which causes report errors and forced sensor resets on ESP32/Pi; "ETIMEDOUT" errors are a symptom. SPI avoids this and is faster; most boards need a PS1 solder bridge for SPI — [bno08x_i2c_spi_MicroPython](https://github.com/bradcar/bno08x_i2c_spi_MicroPython)
- The esp32_BNO08x ESP-IDF driver is SPI-only, citing "unpredictable behavior caused by an esp32 I2C driver silicon bug". It was originally based on the SparkFun BNO080 Arduino library — [myles-parfeniuk/esp32_BNO08x](https://awesome.ecosyste.ms/projects/github.com%2Fmyles-parfeniuk%2Fesp32_BNO08x)
- An Espressif component registry BNO085 driver also exists — [Espressif components: rinku404/bno085](https://components.espressif.com/components/rinku404/bno085/versions/1.0.0/readme)
- ESP32 + GY-BNO080 failures over I2C, and BNO085 at 0x4A responding but failing to initialise, are common forum issues — [Arduino forum: ESP32 + BNO08x](https://forum.arduino.cc/t/esp32-wroom-32-bno08x-imu-gy-bno080-fails-to-return-readings-i-c-setup-help-needed/1390255); [Arduino forum: BNO085 0x4A init fails](https://forum.arduino.cc/t/bno085-responds-at-i-c-address-0x4a-but-initialization-fails-on-arduino-uno-r4-wifi/1452433)
- Adafruit provides Arduino and CircuitPython BNO08x libraries plus UART-RVC libraries; the board has STEMMA QT/Qwiic and a 32.768 kHz crystal — [Adafruit BNO085 guide](https://learn.adafruit.com/adafruit-9-dof-orientation-imu-fusion-breakout-bno085?view=all)
- The ICM-45686 has a 1 MHz I2C, 24 MHz SPI and I3C host interface, an 8 KB FIFO, and an AUX I2C master — [pcbsync ICM-45686](https://pcbsync.com/icm-45686/)
- The LSM6DSV16X SFLP quaternion is written into the FIFO, so it can be batch-read with sensor timestamps — [LSM6DSV16X datasheet](https://cdn.sparkfun.com/assets/4/1/8/e/2/lsm6dsv16x.pdf)
- SlimeVR's open ESP32 firmware (SlimeVR-Tracker-ESP) supports multiple IMU families, including a second IMU per tracker. It is a good code reference for ICM-45686/LSM6DSV drivers, fusion and temperature calibration — [SlimeVR Tracker ESP](https://github.com/sojifes/SlimeVR-Tracker-ESP)

### Inferences
- Most raw IMUs have a selectable address via the SA0/AD0 pin, giving two units per bus. The BNO08x uses 0x4A/0x4B. The MPU6500 on the wrist already uses 0x68, so a second unit on the same bus can go at 0x69 (AD0 high). The classic ESP32 and ESP32-S3 also have two hardware I2C controllers, so each band can get its own bus if the address-strap route is inconvenient. Confirm this against the specific chip's datasheet.
- With an upper-arm IMU on a cable to the wrist ESP32, SPI over a long, flexing cable is riskier than I2C at 400 kHz. Keep cable runs short, or put a small ESP32 on each band and sync wirelessly (ESP-NOW).
- Time sync: if both IMUs share one ESP32, read both FIFOs in the same loop and stamp them with esp_timer. With two ESP32s, use periodic ESP-NOW timestamp exchange. Orientation fusion at 100-200 Hz is ample for arm pose; higher ODR mainly helps gyro integration during fast flicks.

### Gaps
- No primary source was retrieved in this session for the ESP32 two-I2C-controller count or the exact address straps of each IMU. These come from general knowledge and need checking against the datasheets.
- No sourced benchmark was found for multi-IMU time-sync error on ESP32.

## Q4. Prices (approx., Nov 2026 snapshot)

### Takeaway
In India the BNO085 breakout costs about ₹1,750-2,600, the ICM-20948 about ₹760-1,700, and genuine ICM-45686/LSM6DSV breakouts are hard to find locally. Order SlimeVR-style or AliExpress modules, or use the bare chips (about $6) on a custom PCB.

### Cited Findings
- Adafruit BNO085 breakout: $29.50 (qty 1-9) — [Adafruit 4754](https://www.adafruit.com/products/4754)
- Robu.in Adafruit BNO085: ₹2,599 incl. GST, in stock on a staging-mirror page; the main page showed out of stock with 25-30 day restock — [Robu (staging)](https://stgaws.robu.in/product/adafruit-9-dof-orientation-fusion-bno080-stemma-qt); [Robu](https://st.robu.in/product/adafruit-9-dof-orientation-fusion-bno080-stemma-qt)
- Hubtronics BNO085 Nano breakout: ₹1,756.78 + 18% GST — [Hubtronics](https://hubtronics.in/peripheral-modules/bno085-9dof-orientation-imu-fusion)
- ICM-20948: Robocraze 7Semi breakout ₹1,130 (from ₹1,416) — [Robocraze](https://robocraze.com/products/icm-20948-9dof-imu-breakout-board-mpu-9250-upgrade-7semi); Vishaworld ₹758 + GST — [Vishaworld](https://vishaworld.com/products/icm20948-9dof-imu-module); Probots GY-912 ₹1,694 + GST, out of stock — [Probots](https://probots.co.in/gy-912-icm20948-10dof-gyroscope-module-accelerometer-compass-sensor.html)
- BNO055 India breakout ₹400-700 according to a blog guide, not a store listing. Treat this with suspicion, since genuine BNO055 boards are about $38 per SlimeVR — [Zbotic](https://zbotic.in/best-imu-sensors-for-robotics-drones-in-india-2026/)
- ICM-42688 is mostly found on flight controllers in India, not as standalone modules; a TDK Pmod eval board is on DigiKey India — [Zbotic](https://zbotic.in/best-imu-sensors-for-robotics-drones-in-india-2026/); [DigiKey India QCIOT-ICM42688P](https://www.digikey.in/en/products/detail/tdk-invensense/QCIOT-ICM42688P/25676496)
- Bare chips: ICM-45686 about $5.86 and ICM-42688-P about $4.67 single quantity — [pcbsync](https://pcbsync.com/icm-45686/). SlimeVR typical module prices: ICM-45686 about $6.70, LSM6DSV about $5.80, LSM6DSR about $3.35, ICM-42688 about $8, ICM-20948 about $15, BNO055 about $38, MPU6500 about $1 — [SlimeVR](https://docs.slimevr.dev/diy/imu-comparison.html)
- Many cheap "MPU9250" boards actually carry an MPU6500 with no magnetometer — [Microcontrollers Lab buying guide](https://microcontrollerslab.com/best-accelerometer-gyroscope-modules-mpu6050-mpu9250-lsm6ds3-bno085-more-buying-guide/). SlimeVR calls BNO085 listings "very misleading" (clones and fakes) — [SlimeVR](https://docs.slimevr.dev/diy/imu-comparison.html)

### Inferences
- With import duty and shipping, an AliExpress or SlimeVR-store ICM-45686/LSM6DSV module likely lands in India at about ₹700-1,200. That is cheaper than a Robu BNO085 and gives comparable drift with open-source fusion.

### Gaps
- No ElectronicsComp listings surfaced. No SparkFun ICM-45686/LSM6DSV16X or AliExpress prices were retrieved directly.

## Q5. Temperature effects and warm-up drift on skin-worn IMUs

### Takeaway
MEMS gyro bias shifts with temperature, and a skin-worn band heats from room temperature toward about 30-34 °C over the first minutes. The gyro bias therefore walks during warm-up exactly when the user starts moving. Mitigations: per-unit temperature-compensation tables (as SlimeVR does), a warm-up period with still-detection bias re-estimation, and choosing temperature-stable parts (ICM-45686 over ICM-42688).

### Cited Findings
- Biases, scale factors and non-orthogonalities all change with temperature. Thermal calibration can be done by soak or by faster ramp methods — [Fast Thermal Calibration of Low-Grade Inertial Sensors, Sensors 2013](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3821333/)
- Warm-up bias in MEMS gyros is driven mostly by coupling-stiffness variation; suppressing it shortens warm-up and improves bias instability — [Cui et al., Microsystems & Nanoengineering 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6500791/)
- A micro-heater/PID-controlled BMI088 gyro showed better bias repeatability at a controlled 60 °C, and warm-up bias settled in about 50 s on the test rig — [MDPI Sensors 2023, 23(1):256](https://mdpi.com/1424-8220/23/1/256)
- Anecdote: an ST ASM330LHB showed gyro bias jumps when cooling but not when warming (hysteresis); solder stress was suspected — [ST community](https://community.st.com/mems-sensors-48/asm330lhb-chip-shows-large-gyro-bias-jumps-during-temperature-cycling-40-c-to-100-c-127639)
- SlimeVR describes the ICM-42688 as "temperature sensitive and drifts fairly quickly" and the LSM6DSV as "a bit less temperature stable than ICM45686 on paper" — [SlimeVR](https://docs.slimevr.dev/diy/imu-comparison.html)

### Inferences
- For WristTap: log the die temperature, which most of these IMUs expose, alongside gyro bias while stationary during the first 5-10 minutes of wear. Fit a per-unit bias-vs-temperature line and subtract it. Add a thin insulating layer, such as foam or a TPU gap, between skin and sensor to slow thermal transients. Re-estimate bias whenever the stability classifier or a host-side still detector reports rest.

### Gaps
- No study specific to skin-worn or wearable IMU warm-up drift magnitude (deg/min vs time-since-donning) was found. This is worth a quick self-measurement.
