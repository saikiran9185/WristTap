#!/bin/zsh
# Flash the small I2C test, then show 8 s of its report. Run ./flash.sh afterwards to restore WristTap.
cd "$(dirname "$0")"
setopt nullglob
PORTS=(/dev/cu.usbserial* /dev/cu.SLAB_USBtoUART* /dev/cu.wchusbserial* /dev/cu.usbmodem*)
PORT=${PORTS[1]}
[ -z "$PORT" ] && { echo "No ESP32 port found."; exit 1; }
pkill -TERM -f "wristtap.py" 2>/dev/null; sleep 1
~/.local/bin/arduino-cli compile --fqbn esp32:esp32:esp32 firmware/i2ctest || exit 1
echo "Uploading... if it stalls at 'Connecting....', HOLD the BOOT button."
~/.local/bin/arduino-cli upload -p "$PORT" --fqbn esp32:esp32:esp32 firmware/i2ctest || exit 1
~/Projects/PhoneStereo/.venv/bin/python -u - "$PORT" <<'PY'
import serial, sys, time
s = serial.Serial(sys.argv[1], 115200, timeout=0.2); end = time.time() + 25
while time.time() < end:
    l = s.readline().decode(errors="replace").rstrip()
    if l: print(l)
PY
echo "Done. Run ./flash.sh to put the WristTap firmware back."
