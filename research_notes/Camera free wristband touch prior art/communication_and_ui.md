# WristTap: communication from wireless ESP32 band to Mac, and UI design for a projected interface

Context: an ESP32 with 2 IMUs, 4 piezos and 2 FSRs, currently streaming 500 packets/s over USB serial. The goal is a wireless band that tells the Mac/projector where the hand touched the wall and which gesture it made, so the Mac can treat the projection like a touchscreen or mouse.
Raw bandwidth target: 500 Hz × ~40 B = 20 kB/s ≈ 160 kbit/s of payload, before headers. Research date: 15 Nov 2026.

## 1. Transports: Wi-Fi UDP, WebSocket, OSC, BLE GATT, BLE HID, ESP-NOW dongle (latency, jitter, loss, time sync)

### Takeaway
The only controlled cross-transport benchmark found (Electric UI) puts single-packet latency at about 5–6 ms median for ESP-NOW, about 6–9 ms for tuned Wi-Fi TCP/UDP (default config 74–84 ms), about 14 ms for WebSockets, and 14–22 ms for ESP32 BLE notifications. Raw 500 Hz streaming fits within Wi-Fi or ESP-NOW bandwidth. Core Bluetooth on Mac is unpredictable at that rate, so over BLE you should batch samples or send pre-computed events at 50–100 Hz. ESP-NOW to an ESP32 dongle on USB serial is the lowest-latency path that is also the most self-contained. It needs no router, it keeps the existing USB-serial parser on the Mac, and it matches the dongle approach SlimeVR moved to.

### Cited Findings
**Head-to-head latency (Electric UI benchmark: Saleae at 100 MS/s, IRQ-triggered send, pin toggled on receive, more than 200 tests)** — [Electric UI latency comparison](https://www.electricui.com/blog/latency-comparison)
- ESP-NOW (ESP32): about 5.6 ms median for 12 B, about 5.8 ms for 128 B, about 24 ms for 1 KiB (5 packets). Single packets are "consistently ~5 ms".
- Wi-Fi TCP on ESP32 with tuned sockets and Nagle disabled: about 6 ms. Tuned UDP: about 9 ms. Both had outliers up to 25 ms. With the default configuration, every socket test had a median of 74–84 ms.
- WebSockets on ESP32: 14.4 ms (12 B), about 6 ms more than raw TCP. Raspberry Pi 4 WebSockets: 2.3 ms on Ethernet and 6.5 ms on Wi-Fi, with outliers above 50 ms.
- BLE notify (Bluedroid, ESP32): 14.6 ms for 12 B and 21 ms for 128 B. Results fall in bands about 7 ms apart, which matches the 7.5 ms connection interval. Bluedroid write: 20 ms, with outliers above 40 ms.
- NimBLE (ESP32): 45 ms median at first, with outliers up to 150 ms. After an MTU/data-length fix it measured 22 ms (12 B).
- BLE on nRF52840: 13.4 ms, clustered within ±1 ms. Bluetooth Classic SPP on ESP32: about 12.9 ms.
- nRF24 at 2 Mbps: 0.4 ms (12 B). 802.15.4 on ESP32-C6: 2.5 ms.
- USB serial was not tested. Raw 115200-baud UART measured about 1.05 ms, almost all of it byte-transmission time.

**ESP-NOW spread in the field**
- Espressif's outdoor test with an ESP32-C6 measured about 20 ms latency at 30 m and about 35 ms at 150 m in open field, and about 25 ms at 20 m rising to nearly 40 ms at 100 m in forest. ESP-NOW and ESP-NOW-LR results are not cleanly separated in the post — [Espressif blog](https://developer.espressif.com/blog/esp-now-for-outdoor-applications/)
- One user with ESP32-S3 boards reports about 8 ms delay with 4 ms jitter — [esp32.com thread](https://esp32.com/viewtopic.php?p=141153)
- One user reports spikes up to 200 ms with a 50 ms average when sending trajectory points — [espressif/esp-now issue #115](https://github.com/espressif/esp-now/issues/115)
- A design doc estimates ESP-NOW airtime at about 250–400 µs per packet with about 100 µs jitter. This is a calculation, not a measurement — [mlehaptics ESP-NOW vs BLE analysis](https://mlehaptics.readthedocs.io/en/latest/ESP-NOW_vs_BLE_Power_Analysis/)
- Users report that unicast ESP-NOW loses many packets under any Wi-Fi power-save setting other than NONE — [summarised from esp32.com threads via search; see ESP-IDF FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/other-protocols.html)

**Wi-Fi power save and latency**
- Espressif's default mode is `WIFI_PS_MIN_MODEM`. In modem-sleep, receive delay can be as long as the DTIM or listen interval. `esp_wifi_set_ps(WIFI_PS_NONE)` disables it, and the ESP-IDF FAQ recommends this for low latency — [ESP-IDF Wi-Fi performance & power save](https://docs.espressif.com/projects/esp-idf/en/v6.0/esp32c3/api-guides/wifi-driver/wifi-performance-and-power-save.html); [ESP-FAQ protocols](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/other-protocols.html)
- One MicroPython user saw 400–3000 ms MQTT receive latency in the default power-save mode — [MicroPython forum](https://forum.micropython.org/viewtopic.php?p=48585)

**BLE GATT throughput and Apple constraints**
- Apple's Accessory Design Guidelines, as quoted on vendor and forum pages, require Interval Min ≥ 15 ms in multiples of 15 ms, and Interval Max ≥ Interval Min + 15 ms. If you request 15 ms for both min and max, some Apple devices offer 30 ms instead — [Nordic DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/106337/adhering-to-apple-accessory-design-guidelines-for-ble-connection-intervals); [Silicon Labs: Apple connection parameters](https://docs.silabs.com/bluetooth/3.3/bluetooth-miscellaneous-mobile/selecting-suitable-connection-parameters-for-apple-devices)
- Apple DTS on Core Bluetooth (Dec 2024 thread): connection parameters are not guaranteed, and the app is "stuck with whatever iOS will accept". About 600 kbps is reasonable at a 15 ms interval with 2M PHY and MTU 244. For maximum throughput Apple recommends L2CAP CoC rather than GATT. In the same thread, an M3 MacBook and recent iPhones measured 400–600 kbps, unstable, from a peripheral that does 1000–1200 kbps stable on Android and Windows. Problems appeared when the device needed more than about 3–4 packets per 15 ms interval — [Apple Developer Forums 770717](https://developer.apple.com/forums/thread/770717)
- An older nRF report saw only 1 notification received per connection interval on macOS, versus 3 on iOS. This was nRF hardware on an older OS — [Nordic DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/77748/sd_ble_gatts_hvx-duration/321243)
- iOS often gives the connection event only about 50% of a 15 ms interval — [Punch Through](https://punchthrough.com/ble-throughput-part-4/)
- The original ESP32 has only BLE 4.2 hardware: no 2M PHY and no coded PHY, so BLE tops out around 700 kbps theoretical. ESP32-C3 and ESP32-S3 are BLE 5 with 2M PHY and coded PHY (qualified up to 5.4), and the ESP32-C6 is qualified at 5.3 — [ESP-FAQ BLE](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/ble-bt.html); [ESP-IDF BLE feature support (S3)](https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/api-guides/ble/ble-feature-support-status.html); [esp32.com NimBLE throughput](https://esp32.com/viewtopic.php?p=84637)

**BLE HID (band acts as a mouse or digitizer to the Mac)**
- Doublepoint WowMouse turns Wear OS and Apple Watch into a gesture mouse: a pinch clicks and arm motion moves the cursor. It presents as a standard Bluetooth HID mouse, so the host needs no app, and it also offers BLE GATT as an option. No latency figures are published — [Notebookcheck](https://www.notebookcheck.net/Doublepoint-debuts-free-Wow-Mouse-app-transforming-Wear-OS-smartwatches-into-gesture-mice-for-AR-smart-homes-and-more.791532.0.html); [APKMirror release notes](https://apkmirror.com/apk/doublepoint/wowmouse-wear-os/wowmouse-wear-os-0-16-0-release)
- On macOS 14.7, a multi-touch digitizer HID descriptor that worked on Windows did nothing, while a relative mouse descriptor worked. The poster points to Apple's Accessory Guidelines R23 §15 for the digitizer format — [Apple Developer Forums 687740](https://developer.apple.com/forums/thread/687740)
- ESP32 BLE keyboard/mouse projects list relative-mouse compatibility with macOS — [asterics/esp32_mouse_keyboard](https://awesome.ecosyste.ms/projects/github.com%2Fasterics%2Fesp32_mouse_keyboard). Arduino-ESP32 has an absolute-mouse class, but only for USB HID — [arduino-esp32 PR #6331](https://github.com/espressif/arduino-esp32/pull/6331)

**SlimeVR (closest open-source analogue: IMU wearables streaming to a PC)**
- The original ESP trackers talk to the SlimeVR Server directly over 2.4 GHz Wi-Fi, using a UDP protocol encoded with FlatBuffers. They require WPA2, not WPA3 — [SlimeVR tracker protocol](https://awesome.ecosyste.ms/projects/github.com%2Fthebutlah%2Fslimevr-tracker-protocol); [SlimeVR common issues](https://docs.slimevr.dev/common-issues.html)
- The newer "Smol Slimes" use a USB receiver dongle with a proprietary radio for lower latency. The nRF52833 Butterfly trackers use ESB to a dongle with a 100–200 Hz refresh, under 15 ms latency, and up to 48 h battery (specs not final) — [SlimeVR Smol docs](https://docs.slimevr.dev/smol-slimes/); [CNX Software, Feb 2026](https://www.cnx-software.com/2026/02/12/slimevr-butterfly-trackers-nrf52833-based-ultra-slim-full-body-vr-trackers-offer-up-to-48h-battery-life/)

**Time synchronisation**
- SNTP on ESP32 is portable, but asymmetric packet delays hurt its accuracy. Repeating exchanges and averaging (RAMSES) improves it — [TU Wien thesis, Prader 2025](https://repositum.tuwien.at/bitstream/20.500.12708/215541/1/Prader%20Matthias%20-%202025%20-%20Wireless%20Synchronization%20of%20Wearable%20Sensor%20Nodes.pdf)
- SharkTooth (BLE) reaches a median sync error of 0.21–0.62 ms across up to 12 nodes — [search summary of IEEE IoT-J DOI 10.1109/JIOT.2025.3602162]; OpenWiFiSync on ESP32 (Wi-Fi beacons) stays within ±25 µs — [arXiv 2511.14457](https://arxiv.org/pdf/2511.14457)

### Inferences
- Bandwidth: 160 kbit/s is trivial for Wi-Fi or ESP-NOW (one 40 B ESP-NOW frame every 2 ms, or batch 5 samples into one 200 B frame at 100 Hz). Over BLE to a Mac it sits at the edge of what is comfortable. At 15 ms you need about 7.5 samples per interval, about 300 B, which means DLE plus a large MTU, or several notifications per event, and macOS has historically been bad at the latter. The better BLE design is to run tap and gesture detection on the band and send events (touch-down, x, y, gesture ID, confidence) at 50–100 Hz, with raw data only in a debug mode.
- Recommended architecture for WristTap v1: ESP-NOW from band to an ESP32 dongle (any S3, C3 or C6 board) on the Mac's USB. The dongle emits the same serial frames the Mac app already parses. Reasons: about 5 ms latency, no router or venue Wi-Fi needed (useful for exhibitions), and no Mac Bluetooth quirks. SlimeVR also moved from Wi-Fi to a dongle.
- Wi-Fi UDP or OSC is the next choice when a dongle isn't wanted. Set `WIFI_PS_NONE`, disable Nagle if you use TCP, and use a dedicated 2.4 GHz access point or the Mac's hotspot. OSC over UDP feeds TouchDesigner directly. WebSocket adds about 6 ms but lets a browser UI talk to the band with no bridge.
- BLE HID mouse is the easiest "works anywhere" demo, but macOS reliably accepts only a relative mouse. Absolute (x, y) touch from computed wall coordinates would need a digitizer or absolute descriptor, which is unproven on macOS. So put cursor logic in a Mac app (CGEvent) rather than in HID.
- Timestamping: put a 32-bit microsecond band timestamp and a sequence number in every packet. The sequence number gives loss detection. On the Mac, estimate offset with periodic ping/pong round trips (Cristian/NTP-style), keep the minimum-RTT samples, and fit drift linearly. With ESP-NOW and its roughly 5 ms one-way latency, about 1 ms alignment is realistic.

### Gaps
- No controlled measurement of ESP32-S3/C3 BLE notification latency or jitter specifically against macOS (Sonoma, Sequoia, 26) was found. The maximum ATT MTU macOS negotiates was not confirmed.
- No published WowMouse latency, and no SlimeVR Wi-Fi packet-rate or latency figures in the docs (only in firmware source, not examined).
- No packet-loss percentages at 500 Hz for Wi-Fi UDP or ESP-NOW from a controlled source.

## 2. Power: ESP32 draw with Wi-Fi vs BLE, LiPo size for 2–4 h, TP4056, deep sleep, which variant

### Takeaway
Streaming with the radio always on costs roughly 100–150 mA on Wi-Fi or ESP-NOW without power save, versus tens of mA on BLE. A 3 h session therefore needs about a 400–600 mAh cell on Wi-Fi or ESP-NOW, versus about 200–300 mAh on BLE (estimates, see Inferences). The ESP32-C3 and C6 are the wearable picks (single core, BLE 5, small modules). The S3 only earns its place if you need its extra compute or native USB.

### Cited Findings
- ESP32-S3 datasheet-derived peak TX: 340 mA (802.11b, 1 Mbps, +21 dBm), 291 mA (11g 54 Mbps), 283 mA (11n MCS7). Light sleep 380 µA, deep sleep about 7 µA — [Deneyapkart ESP32-S3 power](https://deneyapkart.org/en/docs/guc-tuketimi-esp32-s3)
- ESP32-C3-MINI-1 module: 802.11b TX peak 350 mA (1 Mbps, 21 dBm), RX 82 mA — [ESP32-C3-MINI-1 datasheet (mirror)](https://manuals.plus/m/76b8acb9a27ab293ead4a64ba236492e0f307aa802e985f20d72a2d9eaeb4ff2); official PDF [espressif.com](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf)
- ESP32-C6 figures from a design analysis (not attributed figure by figure to the datasheet): Wi-Fi TX at MCS7 about 130–150 mA, Wi-Fi RX about 95–100 mA, BLE TX/RX at 0 dBm about 17–20 mA, light sleep with Wi-Fi connected about 800 µA, light sleep with BLE connected about 30 µA, deep sleep about 7 µA — [mlehaptics](https://mlehaptics.readthedocs.io/en/latest/ESP-NOW_vs_BLE_Power_Analysis/)
- Measured light sleep on boards: S3 692 µA, C3 193 µA, C6 220 µA — [Qoitech measurement article (search summary)](https://www.qoitech.com/?p=19961)
- One forum user measured modem-sleep at about 50–150 mA, well above the datasheet's roughly 20 mA. BLE streaming on one S3 board drew 85–125 mA total board current — [esp32.com](https://esp32.com/viewtopic.php?p=113049); [ESP32 forum, minimising Wi-Fi power](https://esp32.com/viewtopic.php?p=16969)
- ESP32-S3-WROOM-1 example: deep sleep 8.14 µA, active about 23.9 mA — [ESP-IDF current measurement guide](https://docs.espressif.com/projects/esp-idf/en/v5.3/esp32c3/api-guides/current-consumption-measurement-modules.html)
- TP4056: I_charge = 1200 V / R_PROG. 1.2 kΩ gives 1000 mA (950–1050) and 2.4 kΩ gives 500 mA. Stock modules ship with 1.2 kΩ, which one vendor calls too aggressive for cells under 500 mAh. Charge at about 0.5C, e.g. 2.4 kΩ for a 1000 mAh cell, and scale R_PROG up for smaller cells (around 5–6 kΩ gives roughly 200–240 mA for a 400–500 mAh cell, computed from the formula) — [TP4056 datasheet (LCSC)](https://datasheet.lcsc.com/lcsc/2311091738_UMW-Youtai-Semiconductor-Co---Ltd--TP4056_C725790.pdf); [best-microcontroller-projects](https://www.best-microcontroller-projects.com/tp4056.html); [ShillehTek manual](https://shillehtek.com/blogs/shillehtek-product-manuals/tp4056-1a-lipo-battery-charging-board-type-c-with-current-protection-manual)
- C3 and S3 support BLE 5 2M PHY and the original ESP32 does not (see §1) — [ESP-FAQ BLE](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/ble-bt.html)

### Inferences (estimates, not measurements; verify with a USB power meter or PPK2)
- Budget: MCU active about 25 mA, plus 2 IMUs (a few mA together), plus piezo/FSR front-end (a few mA), plus radio.
  - ESP-NOW or Wi-Fi with `WIFI_PS_NONE` keeps RX on: roughly 100–150 mA total. 3 h × 130 mA ≈ 390 mAh; add 20% margin and that is about 500 mAh (e.g. a 503040 or 603030 pouch, roughly 5×30×40 mm).
  - BLE at a 15 ms interval: roughly 35–60 mA total, so 3 h needs about 180 mAh, i.e. a 250–300 mAh cell.
  - 4 h on ESP-NOW needs about 600–700 mAh, which is bulky for a wrist. A strap-mounted pouch cell, or the BLE events-only design, is the way to shrink it.
- Variant choice: ESP32-C3 (cheap, small modules such as the XIAO ESP32C3 with an on-board LiPo charger, BLE 5, ESP-NOW) or ESP32-C6 (adds Wi-Fi 6 and 802.15.4, the latter measured at 2.5 ms latency in §1). The S3 draws more and costs more, and is only worth it for on-band ML gesture classification. The XIAO boards' built-in charger can replace a separate TP4056.
- Sleep: use the FSR or IMU wake-on-motion interrupt (IMU INT pin to an RTC GPIO) for deep sleep at about 7–10 µA when the band is idle, and light sleep between sessions.

### Gaps
- No authoritative per-chip BLE TX current for C3 or S3 was retrieved (it is in datasheet §"Current consumption depending on RF modes", not fetched). No measured whole-band streaming current from a comparable wearable.

## 3. macOS side: (x, y) to cursor and clicks, HID digitizer, OSC/WebSocket to TouchDesigner/Processing/web, projector homography

### Takeaway
Have a small Mac app (Swift, or Python with pyobjc) receive packets, apply a 4-point homography from wall coordinates to screen pixels, then either post CGEvents (cursor and clicks system-wide; needs the Accessibility/Input Monitoring permission and no App Sandbox) or re-broadcast as OSC/WebSocket for TouchDesigner or browser UIs. Avoid relying on a BLE digitizer descriptor on macOS.

### Cited Findings
- Since macOS 10.14 (Mojave), posting synthetic keyboard and mouse events (CGEventPost) needs explicit user approval under System Settings → Privacy & Security → Accessibility, and does not work in sandboxed apps. Developers report the toggle sometimes needs removing and re-adding after rebuilds — [Apple Developer Forums 103992](https://developer.apple.com/forums/thread/103992); [car-desktop source notes](https://docs.rs/crate/car-desktop/0.13.0/source/src/macos/input.rs)
- To inject events only inside your own app, `NSApplication.postEvent` with synthetic NSEvents avoids the system-wide permission — [Apple Developer Forums 744492](https://developer.apple.com/forums/thread/744492)
- Apple rejected a Mac App Store app for using Accessibility to move the mouse, so distribute outside the store — [Apple Developer Forums 687339](https://developer.apple.com/forums/thread/687339)
- macOS ignored a multi-touch digitizer HID descriptor that works on Windows (macOS 14.7) — [Apple Developer Forums 687740](https://developer.apple.com/forums/thread/687740)
- Synthetic clicks are visible to security tooling, and some secure dialogs block them — [Wardle, "The Mouse is Mightier", DEF CON 26](https://papers.put.as/papers/macosx/2018/DEFCON-26-Patrick-Wardle-The-Mouse-Is-Mightier-Synthetic0Reality.pdf)
- Homography: `cv::getPerspectiveTransform` computes a 3×3 perspective transform from exactly 4 point pairs, and `findHomography` fits more than 4 points robustly — [OpenCV imgproc geometric transforms](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html)

### Inferences
- Pipeline: serial/UDP receiver → filter (One-Euro or similar) → homography H (wall position estimate to projector pixels) → mode switch: (a) CGEvent mouse (`CGEventCreateMouseEvent` with kCGEventMouseMoved / LeftMouseDown / Up, then `CGEventPost(kCGHIDEventTap, …)`), or (b) OSC out (e.g. `/wristtap/touch x y gesture conf`) to TouchDesigner's OSC In CHOP or DAT, or (c) WebSocket to a browser UI. Doing (b) and (c) in the same process lets one band drive both.
- Calibration: project 4 corner targets and have the user tap each. The band's estimated wall coordinates (whatever internal frame: IMU dead-reckoning or piezo TDOA) paired with the known pixel corners give H via getPerspectiveTransform. Add a 5th–9th target to fit `findHomography` and report residual error in cm, which doubles as an accuracy metric for the KAIST/portfolio write-up. Re-calibrate per session because IMU drift accumulates.
- Because the band's error is several cm, also send the confidence/uncertainty radius to the UI so it can size the snapping radius (see §4).
- WristTap's existing PhoneBar, SurfaceTouch and Touch Stage tooling already uses OSC and WebSocket servers on the Mac, so the same pattern applies.

### Gaps
- Apple's official CGEvent and HID digitizer documentation was not fetched. The macOS 26 TCC behaviour for event posting (Accessibility vs Input Monitoring split) was not verified.

## 4. Interaction design for low-accuracy pointing (3–8 cm error)

### Takeaway
Treat the band as a coarse pointer and design targets around its error. Make targets at least 2× the 95% error radius (about 10–16 cm on the wall for 3–8 cm error). Space them so each has a large exclusive capture zone. Use bubble-cursor or nearest-target snapping rather than a raw point cursor. Confirm with a physical tap (piezo spike) rather than dwell. Always show a projected cursor or uncertainty blob, plus a haptic tick on capture.

### Cited Findings
- Bubble cursor (Grossman & Balakrishnan, CHI 2005) resizes the cursor's activation area so the nearest target is always captured. It significantly outperformed both the point cursor and object pointing, and its time is well modelled by Fitts' law using the target's effective width (its Voronoi capture region) instead of its drawn size. Earlier area cursors helped only when targets were sparse — [CHI 2005 paper](https://www.dgp.toronto.edu/papers/tgrossman_CHI2005.pdf); [ACM DOI](https://dx.doi.org/10.1145/1054972.1055012); [HCI museum summary](https://hci-museum.lisn.upsaclay.fr/the-bubble-cursor)
- Finger-touch baselines: Parhi et al. recommend 9.2 mm targets for discrete taps and 9.6 mm for serial taps (one-handed thumb), with error rates flattening above about 7.7–9.6 mm (sources quote both). NN/g recommends at least 1 × 1 cm — [Parhi et al. MobileHCI 2006](https://www.microsoft.com/en-us/research/?p=155150); [NN/g touch target size](https://www.nngroup.com/articles/touch-target-size/)
- Touch on arbitrary surfaces with depth sensing on HoloLens (MRTouch): 5.4 mm mean positional error, and a 16 mm button holds 95% of touches (17 participants, 4 materials). Even a camera-based system needs targets about 3× its mean error for 95% hits — [Xiao et al., MRTouch, IEEE VR 2018](https://robertxiao.ca/pubs/2018_IEEEVR_MRTouch.pdf)
- OmniTouch (wearable depth camera + projector, UIST 2011) also reported its own minimum button size, which was not retrieved here — [OmniTouch PDF](https://modernmobile.cs.washington.edu/docs/omnitouch.pdf)

### Inferences
- Rule of thumb from MRTouch (95% button ≈ 3× mean error): mean errors of 3–8 cm give 95% target diameters of about 9–24 cm on the wall. For a 2 m-wide projection that is 4–10 columns at most, so design "big tile" UIs: 2×3 to 3×4 grids, radial menus, edge targets.
- Use the bubble/Voronoi approach. Each target's selectable area is its whole Voronoi cell, so the drawn button can stay visually modest while the effective width is large. Highlight the captured target, not a raw dot.
- Hysteresis / sticky capture: once a target is captured, require the estimate to move clearly into a neighbour's cell (e.g. 20–30% beyond the boundary) before switching. This stops flicker from noise.
- Confirmation: the piezo or FSR spike at wall contact is a crisp, intentional event (like a mouse click), so use tap = select. Keep dwell (about 600–1000 ms) only as an accessibility fallback. Dwell-only selection is known to cause accidental "Midas touch" selections (common HCI knowledge; no source retrieved here).
- Fitts's law: MT = a + b·log2(D/W + 1). Bigger W and shorter D are the only levers. Put frequent actions near the resting hand position and at screen edges.
- Feedback: (1) projected cursor or uncertainty circle sized to the current confidence; (2) target highlight on capture; (3) a short vibration-motor pulse on capture and a different pattern on confirm. A coin ERM driven via MOSFET or a DRV2605L haptic driver adds about 60–100 mA briefly (typical, unverified here). (4) An optional click sound from the Mac.
- Gestures (swipe, double-tap, press-and-hold from FSR) can carry the precise commands that pointing can't (next/prev, back, zoom), so precision demands on (x, y) drop further.

### Gaps
- Numeric bubble-cursor movement-time gains were not extracted (the PDF could not be text-parsed in this environment).
- No retrieved study of IMU- or acoustic-wristband wall-touch accuracy versus target size, and no retrieved study of haptic feedback effect sizes for mid-air or wall pointing.
