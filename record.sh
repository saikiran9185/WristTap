#!/bin/zsh
cd "$(dirname "$0")" && ~/Projects/PhoneStereo/.venv/bin/python wristtap.py record "$@"
