#!/bin/zsh
# Compile + upload the WristTap firmware to the ESP32 plugged in by USB.
cd "$(dirname "$0")"
setopt nullglob
PORTS=(/dev/cu.usbserial* /dev/cu.SLAB_USBtoUART* /dev/cu.wchusbserial* /dev/cu.usbmodem*)
PORT=${PORTS[1]}
if [ -z "$PORT" ]; then
  echo "No ESP32 port found. Check: data cable (not charge-only), red LED on, try another USB port."
  echo "Ports seen:"; ls /dev/cu.*; exit 1
fi
echo "ESP32 on $PORT"
~/.local/bin/arduino-cli compile --fqbn esp32:esp32:esp32 firmware/wristtap || exit 1
echo "Uploading... if it stalls at 'Connecting....', HOLD the BOOT button on the ESP32 until it starts writing."
~/.local/bin/arduino-cli upload -p "$PORT" --fqbn esp32:esp32:esp32 firmware/wristtap && echo "DONE. Now run: ./check.sh"
