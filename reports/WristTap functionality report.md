# WristTap: everything it can do

*15 Nov 2026. Based on the working breadboard build (all 8 sensors tested) and two research reports in this folder:*
- *IMU drift fixes for hand tracking.md*
- *Camera free wristband touch prior art.md*

---

## 1. What each sensor gives you

| Sensor | Count | What it feels | What it's good for |
|---|---|---|---|
| Motion sensor (MPU) on the wrist | 1 | tilt, turning, flicks, shakes | cursor movement, rotation, gestures |
| Motion sensor (MPU) on the upper arm | 1 | upper-arm angle | arm model, so the Mac can estimate where the hand is |
| Piezo discs on the wrist skin | 4 | the tiny shock of a tap or pinch | **click**, touch moment, which finger tapped |
| Force sensors (FSR) under the strap | 2 | tendons tightening | **press strength**, hold, grip |
| ESP32 | 1 | — | sends 500 packets a second to the Mac (USB now, wireless later) |

**The basic rule:**
- The band is very good at **WHEN** (a touch happened) and **WHAT** (which gesture).
- It's good at **HOW MUCH** (press strength) and **HOW IT MOVES** (relative movement).
- It's weak at **WHERE** in the room (absolute position), because motion sensors drift.

---

## 2. Mode A: Air mouse for the laptop ⭐ easiest, works with today's parts

This needs no absolute position. It moves the cursor like a mouse: your eyes correct it, so drift doesn't matter. Products such as Doublepoint WowMouse and Mudra Band prove the idea works.

| You do | Sensor | The Mac does |
|---|---|---|
| Tilt or turn your wrist | wrist MPU | move the cursor |
| Quick pinch (thumb taps index) | piezos + FSR | left click |
| Double pinch | piezos | right click |
| Pinch, hold and move | FSR held + MPU | drag, select, draw |
| Pinch and twist your forearm | FSR + MPU roll | rotate an object or knob |
| Pinch and tilt up or down | FSR + MPU | scroll, or zoom |
| Flick left or right | MPU spike | back / forward, next / previous slide |
| Drop or relax your hand | MPU (arm down) | pause the cursor so it doesn't wander |
| Press harder | FSR level | stronger action (e.g. brush size, volume) |

**Setup (about 10 seconds):**
1. Hold still for 2 seconds. The Mac removes the sensor offset.
2. Pinch 5 times. The Mac learns how strong your pinch is.

**Limits:**
- Typing or bumping the desk can cause false clicks until it's trained on your own data.
- It's less precise than a real mouse: fine for buttons and dragging, not pixel work.

---

## 3. Mode B: 3D and creative apps

These fit projects you already have.

| App | What WristTap controls |
|---|---|
| **Blender** (like DualHand) | pinch + twist to orbit a model, pinch + tilt to zoom, flick to undo |
| **TouchDesigner** (your HTTP bridge, phone-OSC cube) | stream all 8 sensors as OSC: wrist angle → rotation, FSR → intensity, tap → trigger |
| **Music / VJ** | 4 piezos = 4 drum pads (tap strength = loudness), FSR = expression / filter, wrist roll = knob |
| **Presentations** | flick = next / previous slide, pinch-hold = laser pointer dot, double pinch = black screen |
| **Media** | pinch = play / pause, twist = volume, flick = next track |

---

## 4. Mode C: Touching a projected wall (the big goal)

### C1. Band only (no camera, no extra hardware)
- **How:** an arm model computes the hand position from the upper-arm and forearm angles. You touch the 4 corners to calibrate. Each later touch on a known button resets the drift.
- **Accuracy:** about 2 cm right after a reset. It then drifts about 1.2 cm per degree of heading error, and needs a re-tap if you step or lean.
- **UI rule:** big tiles (about 9–24 cm), a cursor that snaps to the nearest tile, and a tap to confirm.
- **Good for:** menus, big buttons, games, sliders. Not for small text or fine drawing.
- **Status:** nobody has published this exact system, so WristTap would be new. We have to measure its real accuracy ourselves.

### C2. Band + one small camera-free helper (exact position, works in the dark)
| Helper | Accuracy | Cost | Notes |
|---|---|---|---|
| **Ultrasound mic bar** (eBeam style): band sends a chirp + radio sync, 2–3 mics at the wall corner | a few cm or better (mm in research) | ₹500–2,000 | best fit; same idea as old eBeam projector pens |
| **4 piezos on a hard projection board** | 2.5–4 cm | under ₹1,500 | needs glass, acrylic or MDF, not plaster |
| **UWB radio anchors** | about 10 cm, in 3D | ₹10–25k | good for room-scale hover, too coarse alone |
| Projector light codes + photodiode | exact pixel | about ₹50 | uses light (flicker), so it breaks the "no light" rule |

### What the wall mode can do
- tap = click, press harder = stronger action, hold = drag
- hover (hand near the wall, no touch) = show a cursor blob, no click
- gestures anywhere = commands (undo, menu, next page)

---

## 5. Mode D: Gesture remote (no screen pointing at all)

About 5–8 trained gestures, each mapped to any Mac shortcut:
- pinch, double pinch, fist squeeze (FSR), flick left / right, wrist roll left / right, tap with different fingers (4 piezos)
- **Use cases:** control music while cooking, slides while presenting, lights or TouchDesigner scenes during a performance

---

## 6. Mode E: Data and research

- **Record** all sensors with camera labels (`./record.sh`). The camera is used only during training, then a model runs without it.
- **Study** grip strength, tap timing and hand tremor over time (FSR + piezo + MPU).
- **Portfolio / HCI research:** a measured "camera-free projected touch" result would be new, and fits the KAIST HCI direction.

---

## 7. How it talks to the Mac

| Stage | Link | Delay | Notes |
|---|---|---|---|
| Now | USB cable, 921600 baud | very low | works today (`./check.sh`) |
| Next | **ESP-NOW** → second ESP32 plugged into the Mac | about 5–6 ms | recommended: no router, no pairing |
| Option | Wi-Fi UDP / OSC | about 6–9 ms (tuned) | direct to TouchDesigner |
| Option | Bluetooth HID mouse | about 15–20 ms | Mac sees a normal mouse; relative movement only |

**On the Mac:** a small program reads the stream, recognises gestures and moves the cursor or clicks (needs Accessibility permission once). It can also send OSC/WebSocket messages to TouchDesigner, Blender or a web app.

**Battery for wireless:** about 500 mAh LiPo + TP4056 charger for about 3 hours (an estimate, to check). ESP32-C3 or C6 suit a wearable.

---

## 8. What works now vs what needs work

| Feature | Status |
|---|---|
| Live readings of all 8 sensors | ✅ working |
| Tap detection on 4 piezos | ✅ working |
| Press detection on 2 FSRs | ✅ working |
| Air mouse (cursor + pinch click) | 🔧 Mac software only, no new parts |
| Gesture recognition (5–8 gestures) | 🔧 software + recording your own training data |
| Better tap types (which finger) | 🔧 firmware: piezo sampling from 500 to 2,000+ per second |
| Calibration (fixes the 1.08 g reading) | 🔧 firmware + Mac software |
| Wireless | 🛒 second ESP32 (have it) + battery + charger |
| Wall touch, band only | 🔧 arm-model software + tap-grid accuracy test |
| Wall touch, exact | 🛒 ultrasound mic bar or piezo board |
| Less drift | 🛒 ICM-45686 or LSM6DSV sensors (~$6–7 each) |
| Wearable body | 🖨️ 3D-printed bangle + upper-arm band |

---

## 9. Suggested order

1. **Air mouse on the laptop.** It's the quickest demo, with no new parts, and it shows which gestures feel good.
2. **3D-printed bangle**, designed around the gestures that worked.
3. **Calibration + faster piezo sampling** (firmware).
4. **Gesture training** (record your own data, small model on the Mac).
5. **Wireless** (ESP-NOW dongle + battery).
6. **Wall mode, band only:** 4-corner calibration, then the tap-grid test to measure real accuracy.
7. Based on that number, **add the ultrasound bar** if exact position is needed.
