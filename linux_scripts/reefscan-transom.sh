#!/usr/bin/bash
# This script runs reefscan-desktop-data-manager in "transom" mode
# "transom" changes the IP address of the reefscan device to match the standard IP address
# for a reefscan-transom device, which is 192.168.2.3
# the script is copied to the desktop by setup.sh and can be run by double clicking on it
# this works in Ubuntu 20
source ~/.reefscan_env
cd $REEFSCAN_HOME/reefscan_desktop_data_manager
. ./venv/bin/activate
export PYTHONPATH="$REEFSCAN_HOME/reefscan_desktop_data_manager/real_src/:$PYTHONPATH"
python3 src/main.py
cd
