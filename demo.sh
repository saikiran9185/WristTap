#!/bin/zsh
# WristTap live demo. ./demo.sh (USB) | ./demo.sh --ble | ./demo.sh --wifi
cd "$(dirname "$0")" && ~/Projects/PhoneStereo/.venv/bin/python demo.py "$@"
