#!/bin/bash
# Wait for desktop to load
sleep 10

# Start the app
cd /home/dhanunjay1729/contest-reminder
source venv/bin/activate
python contest_gui.py
