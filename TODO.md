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
