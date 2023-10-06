#!/bin/bash
cd /home/reefscan/reefscan/reefscan_desktop_data_manager
. ./venv/bin/activate
export PYTHONPATH="/home/reefscan/reefscan/reefscan_desktop_data_manager/real_src/:$PYTHONPATH"
python3 src/main.py
cd /home/reefscan
