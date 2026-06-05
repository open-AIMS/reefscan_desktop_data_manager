#!/usr/bin/bash
source ~/.reefscan_env
cd $REEFSCAN_HOME/reefscan_desktop_data_manager
. ./venv/bin/activate
export PYTHONPATH="$REEFSCAN_HOME/reefscan_desktop_data_manager/real_src/:$PYTHONPATH"
python3 src/main.py deep
cd
