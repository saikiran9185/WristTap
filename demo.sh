#!/bin/zsh
# WristTap live demo. ./demo.sh (USB) | --ble | --wifi | --sim (fake band). Press S on the page for Show mode.
cd "$(dirname "$0")" && ~/Projects/PhoneStereo/.venv/bin/python demo.py "$@"
