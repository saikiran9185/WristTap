#!/bin/zsh
# WristTap 3D mouse. ./space.sh (USB) | ./space.sh --ble | ./space.sh --wifi
cd "$(dirname "$0")" && ~/Projects/PhoneStereo/.venv/bin/python space.py "$@"
