#!/usr/bin/env bash
cd /home/fer-dev/ROBOT-PI-EJECUTION || exit 1
python3 robot-pi/scripts/runtime_control_terminal.py
exec bash
