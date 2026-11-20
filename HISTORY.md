# WristTap: project history

A wristband that senses finger taps, squeezes and arm movement and controls a Mac with them.
Gesture-Based Interaction coursework, B.Design, November 2026.
This file records everything that was tried, what worked, what did not, and what is still open.

## The hardware

| Part | Where | Pin | Notes |
|---|---|---|---|
| ESP32 DevKit V1 (30-pin) | forearm tray, USB at the elbow | – | USB 500 packets/s · Wi-Fi UDP 4210 500/s · Bluetooth LE "WristTap" 100/s |
| MPU #1 (MPU6500 clone, 0x68) | forearm | SDA D21 · SCL D22 | AD0 → GND |
| MPU #2 (MPU6050, 0x69) | back of hand | same bus | AD0 → 3V3 |
| 4 piezo discs P0–P3 | around the wrist | D32 · D33 · D34 · D35 | each: 1 MΩ to ground + 10 kΩ in series |
| 2 FSR strips F0/F1 | forearm | VP (36) · VN (39) | each: 10 kΩ to ground |

As worn (left arm, palm down): **P2 = top of the wrist, P3 = thumb side, P0 = palm side, P1 = little-finger side.**

## Timeline

### 14–15 Nov: parts and the breadboard prototype
- Parts list, build guide (`assemble.html`, `guide.html`, `parts.html`, PDFs) and test pages for every sensor.
- Firmware `firmware/wristtap/`: one 44-byte packet per sample (`\xaa\x55` magic) with both MPUs, 4 piezo peaks and 2 FSRs.
- Mac reader `wristtap.py` (`./check.sh` live values, `./record.sh` recording) and spoken tap/press tests (`taptest*.py`, `fsrtest.py`).
- **All 8 sensors working** on the breadboard (photo `photos/11-all-sensors-working.jpg`).
- Research: `reports/IMU drift fixes for hand tracking.md` and `reports/Camera free wristband touch prior art.md`.

### 17 Nov: v2, wearable shells + wireless
- `cad/band.scad`: closed forearm box, hand shell, piezo and FSR pods (`print_package/`).
- Firmware streams over USB, Wi-Fi and Bluetooth LE. `demo.py` / `demo.html`: live 3D arm, taps, squeezes, flicks, air mouse on `localhost:8791`.
- `setup.html` (now `wiring-setup.html`): click-through mini-breadboard guide with live sensor checks.

### 18 Nov: printed tray and pods (exam prototype)
- `cad/sled.scad`: open tray for half breadboard + ESP32, MPU #1 bay, engraved labels, P/F pods, MPU #2 hand holder (2 h 04, 57 g).
- `cad/watch.scad`: a one-piece small band (1 h 38, 48 g), kept for the soldered version.
- `placement.html`, `paper/` A4 paper dieline, `solder.html` guide for later.
- Band worn and connected over Bluetooth.

### 20 Nov: wearable rewire, demo, settings, recording
- Worn band was an unwearable tangle of long jumpers. **`rewire.html`**: rebuilds the breadboard from empty, one wire per screen (70 steps, live checks), drawn as the real upright board.
- Reader auto-reconnects when USB is unplugged; the demo reports "no data" instead of freezing.
- **Show mode** in `demo.html` (press S): 9 captioned steps, webcam view of the hand (C), proof strip with live signal traces.
- Slide deck "WristTap: How It Works" (12 slides, Claude artifact).
- **`config.html` Settings page** (`/config`): disc places, arm and hand directions, squeeze (FSR) numbers, background noise, false-trigger filters, gesture lab (test each gesture ×5, see what else fired, one-click fixes). Everything saved to `calib.json`.
- **`setup.html` Setup tutorial** (`/setup`): 13 guided steps; a yellow guide arm shows each move, you repeat it 3 times, the majority result is saved. Records the screen and camera.
- **`play.html` Try it** (`/play`): practical use. *Presenting* (flick = next/previous slide, double tap = black screen; real arrow keys, so it works in Keynote/PowerPoint) and *Real UI control* (hand = cursor, tap = click, double tap = double-click, squeeze-hold = drag, wrist roll = scroll).
- Full-screen recording from any page (● Record) → `photos/WristTap_demo_*.mov`.
- First demo take: `photos/WristTap_demo_20261120.m4v` (720p copy; Show mode, before calibration).

## Bugs found and fixed (20 Nov)

| Problem | Cause | Fix |
|---|---|---|
| 3D arm swung on its own while the band lay still | Sensors sit near roll ±180°; the filter averaged +179° and −179° as far apart | Filter and display now take the short way round the circle |
| Arm shook when still | Raw angles | One-Euro adaptive smoothing (`smooth_hz`), no lag on fast moves |
| "Roll right" then "Roll left" for one roll | The hand coming back looked like the opposite gesture | `return_ms` window + re-arm rule; single-sample spikes averaged out |
| One tap fired neighbouring discs | Vibration spreads through the band | Filters: one disc per tap, bump, echo, motion and lock windows; ignored triggers logged with a reason |
| Settings didn't show on the demo arm | Pages read `calib.json` once at load | Server broadcasts every settings change to all open pages |
| Flick directions ignored calibration | Raw gyro axes | Flicks and roll use the learned hand directions |
| FSR test on spare ESP32 read a false 4095 | `analogRead` turns off the internal pull-down | `firmware/fsrsolo/`: re-enable it with `rtc_gpio_pulldown_en` |

## What worked
- All 8 sensors read correctly on the bench; both MPUs and all 4 discs work worn.
- Bluetooth streaming at ~100 packets/s, good enough for gestures and the air mouse.
- Taps on each disc, flicks, wrist roll and the 3D arm, after calibration.
- The band sends real keys and mouse events, so it controls any app.

## What did not work / still open
- **F1 (FSR on VN, row 5) reads 0 on the band.** The strip is fine (tested alone on the spare ESP32), so the row-5 wiring is at fault. Unresolved.
- **Desk vibration causes false taps** when the band lies on a table next to the keyboard; much less of a problem worn.
- **Breadboard + jumpers are fragile when worn**: long loops pull the sensors and wires come loose. The fix is the soldered small band (`watch.scad`, `solder.html`), not started.
- **Yaw (swing) drifts** with no magnetometer; it needs re-centring. The drift report suggests ICM-45686 / LSM6DSV sensors and a VQF filter.
- The demo video was recorded before calibration; a calibrated take with the Try-it page is still to do.

## If continuing
1. Fix F1's row-5 wiring, or move it to another analog pin.
2. Run `/setup` once, test every gesture in the lab on `/config`, then record the Try-it page.
3. Solder the small band: shorter wires, no breadboard, tape strain relief on both MPUs.
4. Raise piezo sampling (2 kHz+) and consider better IMUs for less drift.

## How to run
```
./demo.sh --ble --no-open      # or --sim for a fake band, or no flag for USB
open http://localhost:8791/setup    # guided setup (3× per move)
open http://localhost:8791/config   # all settings + gesture lab
open http://localhost:8791/play     # presenting + real UI control
open http://localhost:8791/         # live demo, Show mode (S), camera (C), record (R)
```
