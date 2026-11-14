I'm building WristTap, a wrist band with sensors that talks to my Mac. I'm stuck on build step 3, "Sensor 1": MPU6050 #1 does not show up. Help me get IMU1 working. Go one wire at a time, and check facts in my files before telling me anything.

## Project
- Folder: ~/Projects/WristTap
- Firmware: firmware/wristtap/wristtap.ino (ESP32, raw I2C, Wire.begin(21, 22), 400 kHz; IMU addresses 0x68 and 0x69; retries a missing IMU every 0.5 s)
- Mac reader: wristtap.py. `./check.sh` runs `wristtap.py check` with the Python in ~/Projects/PhoneStereo/.venv and prints one line per second.
- Build guide: assemble.html (interactive; the ITEMS list near line 197 has every wire), guide.html, parts.html, WristTap_Build_Guide.pdf (made by render_pdf.swift; NOT regenerated after my edits)
- Serial port: /dev/cu.usbserial-0001

## Hardware
- ESP32 DevKit (30 pins). Right header, top to bottom: D23, D22, TX0, RX0, D21, D19, D18, D5, TX2, RX2, D4, D2, D15, GND, 3V3. So D22 is the 2nd pin and D21 is the 5th: they are 3 pins apart.
- GY-521 MPU6050 board, pressed onto pins with NO solder (contact can be loose)
- Half-size breadboard. Columns a–e | gap | f–j. Each coloured rail line is one strip from top to bottom.
- IMPORTANT: the rail lines have NO hole at every 6th spot (6, 12, 18, 24). See assemble.html line 151: `railHas = n => n % 6 !== 0`. Check this before you name any rail hole.
- In the guide: T+ = LEFT red line (3V3), T- = LEFT blue line (GND), B- = RIGHT blue (GND), B+ = RIGHT red (not used).

## Step 3 wiring (as the guide says now)
MPU #1 sits in column a, rows 3–10, body pointing LEFT over the rail lines. Pins by row: 3 INT, 4 AD0, 5 XCL, 6 XDA, 7 SDA, 8 SCL, 9 GND, 10 VCC.
Step 2 (done): ESP32 3V3 → red line 1, ESP32 GND → blue line 1 (plus left GND → right blue line 1).
| Wire colour | From | To |
|---|---|---|
| yellow (SCL) | ESP32 D22 | c8 |
| blue (SDA) | ESP32 D21 | c7 |
| red (VCC) | b10 | red line 11 |
| grey (GND) | b9 | blue line 11 |
| white (AD0) | b4 | blue line 13 |
AD0 wire history: the original guide said blue line 2, but the MPU body covers it. Then 12 was suggested, but that spot has no hole (mistake). Now it's 13. I currently have it in blue line 14. That works electrically, but MPU #2 goes in rows 14–21 in step 4, so move it to 13.
Step 4 (later): MPU #2 in a14–a21, SCL b19→e8, SDA b18→d7, VCC b21→red 22, GND b20→blue 22, AD0 b15→RED 13 (address 0x69).

## Current state (14 Nov 2026, about 16:15)
- The MPU's LED is ON, so it has power.
- ESP32 streams fine: about 500 pkt/s.
- Every check line says: `IMU1 MISSING (check wiring / AD0)  IMU2 MISSING (check wiring / AD0)`. IMU1 has never appeared, not even once in about 1.5 h of readings. IMU2 missing is expected (not built yet).
- Both missing means the ESP32 gets no I2C answer at all. A wrong AD0 would show IMU2 instead, so AD0 is not the cause.
- Suspects, in order: (1) yellow/blue on the wrong ESP32 pins (in my photo they looked only 1–2 pins apart, not 3); (2) SDA/SCL swapped; (3) MPU pins not touching (no solder); (4) wires on the f–j side of the gap instead of a–e.
- Fresh check at about 16:25 (old reader stopped): 500 pkt/s, 0 drops, IMU1 MISSING, IMU2 MISSING. Piezo around 820–1270, FSR around 865–1015: normal noise from empty pins. (A 4095 piezo reading seen in an old run is gone; ignore it.)
- Tip: `timeout 8 ./check.sh | tail` prints nothing (output is buffered). Run `python -u wristtap.py check` in the background to a file, stop it with `pkill -INT -f "wristtap.py check"`, then read the file.
- Visual explainer of step 3 (rows, strips, check.sh reader): https://claude.ai/artifact/Hp489z8jSDBpUCZj94CmDQ

## What would help next
- Maybe add an I2C bus scan to the firmware (print every address that answers). That would show whether the bus sees nothing or something at an unexpected address. Ask me before flashing (./flash.sh).
- Ask me for a sharp close-up photo of the ESP32 header where the yellow/blue wires plug in, with pin labels readable, instead of guessing from blurry photos.

## How to work with me
- I'm a design student, not an electronics engineer. Use short, simple sentences: one step at a time, and say exact hole names (e.g. "c7", "blue line 13").
- Never guess hole numbers or pins: check them against assemble.html / the firmware first. If a photo is blurry, say so and ask for a better one.
- After each change, tell me what result to expect from ./check.sh (success = `IMU1 |a| ≈ 1.00 g`, peak jumps when shaken).
- Browser: only Dia (`open -a /Applications/Dia.app`), never headless.
