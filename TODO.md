# WristTap: plan after printing (18 Nov)

## Done
- [x] All sensors work on the breadboard (MPU #1, MPU #2, 4 piezos, 2 FSRs)
- [x] Firmware: USB + Wi-Fi + Bluetooth LE streaming, live demo (./demo.sh)
- [x] 3D print: all parts printed

## Next, in this order
- [ ] **1. Make it shorter**: details still to write down (wires? band? which part, by how much?)
- [ ] **2. Shopping**: check SHOPPING_LIST.txt, buy only what is missing
- [ ] **3. Baseline test before rewiring** (./check.sh, tap every disc, press every FSR)
- [ ] **4. Reconnect the breadboard version**: follow setup.html (one half breadboard, 30 rows)
  - [ ] Power lines · check: LED on, 500 pkt/s
  - [ ] MPU #1 · check: IMU1 ≈ 1 g
  - [ ] MPU #2 · check: both ≈ 1 g
  - [ ] Piezo 0 · check: tap → hundreds
  - [ ] Piezos 1–3 · check: taptest_all.py diagonal
  - [ ] FSRs · check: 1000–4000 pressed
- [ ] **5. Fit the breadboard + sensors into the printed parts** (placement.html)
- [ ] **6. Demo over Bluetooth** (./demo.sh --ble)
- [ ] **7. Record a test with camera labels** (./record.sh)

## LATER: soldered version
Saved in solder.html (header-pin hubs, resistors in the wires, tape). Do it after the demo.
