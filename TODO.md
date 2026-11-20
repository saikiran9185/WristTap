# WristTap: wearable → demo → record (20 Nov)

Guide: rewire.html (one wire per step, live checks: run ./demo.sh --no-open first). Demo: ./demo.sh --ble, press S for Show mode. Slides: https://claude.ai/artifact/9gA5RVtpDdc1ZqQFfx6a4F

- [ ] **1. Rewire inside the printed tray** (rewire.html: Start → MPU 2 power) · who: you · needs: nothing
      → gives: FSRs at rows 3/5, both MPUs at rows 27–30, all 8 sensors live in ./check.sh
- [ ] **2. Make it flat** (rewire.html "Make it flat") · who: you · needs: 1 → gives: nothing higher than the ESP32, pins taped
- [ ] **3. Harnesses + tape anchors + cover** (rewire.html "Straps") · who: you · needs: 2 → gives: no loose loops
- [ ] **4. Strap on + worn stress test** (rewire.html "Wear") · who: you, I read check.sh · needs: 3
      → gives: no sensor drops out while bending, fisting, shaking
- [ ] **5. Rehearse Show mode** (./demo.sh --sim, then --ble) · who: you · needs: 4 for --ble
- [ ] **6. Record 2–3 takes** · who: you · needs: 5 → gives: demo video
- [ ] **7. Video into slides + README** · who: me · needs: 6

---
## Older (18 Nov)
# WristTap: record the demo, then solder a small single band (18 Nov)

Goal 1 (today): a demo video showing that the worn band moves the cursor and the 3D arm, and that taps/presses work.
Goal 2 (after recording): solder version = one small band, no breadboard, shorter wires.
Buffer: record BEFORE taking anything apart. Once it's apart, there's no going back to film.

### Phase 1: record the demo (band still on, Bluetooth)
- [ ] **1. Fix any backwards directions** · who: you tell me, I fix · when: now
      needs: nothing → gives: the cursor and the 3D arm move the right way
      Tell me only the wrong ones: cursor L/R, cursor up/down, arm roll, arm tilt, arm swing
- [ ] **2. Set up the shot** · who: you · when: now
      needs: 1 → gives: one camera frame showing your arm AND the Mac screen together
      Phone on a stand behind your shoulder, screen bright, demo page full screen (Cmd+Ctrl+F), power bank in your pocket, NO USB cable (shows it's wireless)
- [ ] **3. Rehearse the script once** (~60 s) · who: you · needs: 2 → gives: a smooth take
      a) Click Recenter b) roll the wrist, tilt the hand, swing the arm (3D arm follows)
      c) air mouse: move the cursor round the screen d) tap discs 0→3, then a double tap
      e) squeeze FSR 0 and FSR 1 f) a flick
- [ ] **4. Record 2–3 takes** · who: you · needs: 3 → gives: the demo video
      Optional extra: also screen-record at the same time (Cmd+Shift+5) for a clean screen-only version
- [ ] **5. Save the best take into the project** · who: you AirDrop, I file it · needs: 4
      → gives: video in ~/Projects/WristTap/photos/, linked in the README and pushed to GitHub

### Phase 2: soldered small band (starts after 5)
- [ ] **6. Decide what goes in the small band** · who: you · needs: nothing
      → gives: the parts list the new band is designed around
      a) all sensors (2 MPU + 4 discs + 2 FSR), or fewer? b) keep this ESP32, or order a tiny board (XIAO ESP32-S3, ~21x18 mm, needs delivery)?
      c) power: power bank on a strap, or a small LiPo battery? d) what did you mean by "pico holke"?
- [ ] **7. I redesign the one-piece band for no breadboard** (watch.scad) · who: me · needs: 6
      → gives: a shorter, smaller printable band + a 1-plate print file
- [ ] **8. Send the print to your friend** · who: you · needs: 7 → gives: printed band (runs in the background, ~1.5 h)
- [ ] **9. Gather solder kit** · who: you · needs: 6
      → gives: iron, solder, insulation tape, 2 header-pin strips (red 3V3 hub, black GND hub), thin wire
- [ ] **10. Take the band apart** · who: you · needs: 5 (video saved!) → gives: loose sensors + resistors
- [ ] **11. Solder, one sensor at a time, test after each** (solder.html, 10 steps, ~2 h) · who: you, I run the checks
      needs: 9, 10 → gives: a working circuit with short wires, no breadboard
- [ ] **12. Fit into the printed band + worn test** (`./check.sh`, then `./demo.sh --ble`) · who: you + me
      needs: 8, 11 → gives: the small single band to show

---
## Old: wearable assembly list (done 18 Nov, band worn + Bluetooth connected)
# WristTap: put the printed parts together (demo today, 18 Nov)

Printed set: tray + P0–P3 + F0/F1 + MPU #2 HAND (names are engraved on each). Left arm, palm down.
Buffer: be fully assembled 1 h before the demo so there's time to fix a loose wire.

### Phase A: before touching the arm
- [ ] **A1. Check every part fits (no wires yet)** · who: you
      needs: nothing → gives: proof everything drops in; anything too tight gets reprinted now
      Breadboard into the big window pocket · ESP32 onto the rib frame (pins down, USB at the ELBOW end hole) · MPU into the MPU #1 bay · disc into each P pod · FSR pad into each F pod · MPU #2 into HAND · 25 mm strap through every slot
- [ ] **A2. Baseline test on the table** (`./check.sh`, tap every disc, press both FSRs) · who: you
      needs: wiring done (old steps 4–9 below) → gives: proof all sensors work before they go in plastic

### Phase B: load the tray
- [ ] **B1. Breadboard in** · USB unplugged. Foam/double tape under it, row 1 at the ESP end
- [ ] **B2. ESP32 in** · onto the rib frame, jumper plugs hang between the ribs, USB faces the elbow hole
- [ ] **B3. MPU #1 in** · wrist-end bay, flat, tape under it, pins sideways (arrow "PINS >")
- [ ] **B4. Tape the jumpers** · strip of tape over the ESP32 pin rows (a shake knocks them out)

### Phase C: load the pods
- [ ] **C1. Discs into P0–P3** · brass side DOWN (skin side), tape loop on the rim, wire out along the strap
- [ ] **C2. FSRs into F0/F1** · pad down (skin side), tail out towards the tray
- [ ] **C3. MPU #2 into HAND** · flat, tape under it, ribbon towards the wrist

### Phase D: on the arm
- [ ] **D1. Thread straps** · tray: 2 straps through the 4 side slots. F0 + F1 onto the ELBOW-end strap
- [ ] **D2. Wrist strap** · thread P0 → P1 → P2 → P3, then close it just below the wrist bones, firm
      P0 little-finger bump · P1 palm side · P2 thumb bump · P3 back of wrist
- [ ] **D3. Tray on** · top of forearm, MPU #1 end ~1.5 cm behind the wrist strap; F0/F1 sit side by side on the soft inner forearm
- [ ] **D4. Hand holder on** · back of hand, ~2 cm behind the knuckles, strap round the palm
- [ ] **D5. Tidy wires** · bundle each sensor's wires along the strap to the tray, tape so nothing loops; make a fist + bend the wrist: nothing should pull tight

### Phase E: final checks
- [ ] **E1. Worn test** (`./check.sh`): both IMUs ≈ 1 g, every disc reacts, FSRs 1000–4000 pressed
- [ ] **E2. Demo rehearsal** (`./demo.sh --ble` with power bank, or plain `./demo.sh` on USB)

---
## Wiring (needed before A2)
# WristTap: one half breadboard, 30 rows (no solder)

Deadline: demo tomorrow (18 Nov). Guide: setup.html (click-through, live checks). Reference: minibb.html.

- [ ] **1. Tell your friend: skip the big box + lid** · who: you · needs: nothing → gives: pods + hand shell
- [ ] **2. Baseline test** (./check.sh, tap every disc, press every FSR) · who: you → gives: proof all sensors work before rewiring
- [ ] **3. Pull every wire off both boards, keep sensors + resistors** · who: you · needs: 2
- [ ] **4. Power lines** (minibb step 1) · check: LED on, 500 pkt/s
- [ ] **5. MPU #1** · check: IMU1 ≈ 1 g
- [ ] **6. MPU #2** · check: both ≈ 1 g
- [ ] **7. Piezo 0** · check: tap → hundreds
- [ ] **8. Piezos 1–3** · check: taptest_all.py diagonal
- [ ] **9. FSRs** · check: 1000–4000 pressed
- [x] **10. Cut the board**: dropped, using all 30 rows (18 Nov)
- [ ] **11. (optional) Me: shrink the printed box to fit ESP32 + mini board** · needs: 10 decided
- [ ] **12. Demo over Bluetooth** (./demo.sh --ble)

## LATER: soldered version
Saved in solder.html (header-pin hubs, resistors in the wires, tape). Do it after the demo.
