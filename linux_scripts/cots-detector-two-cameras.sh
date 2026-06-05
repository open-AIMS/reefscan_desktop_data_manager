#!/bin/bash
source ~/.reefscan_env
 
$REEFSCAN_HOME/reefscan_desktop_data_manager/linux_scripts/cots-detector.sh "$1/cam_1" "$2/cam_1"
$REEFSCAN_HOME/reefscan_desktop_data_manager/linux_scripts/cots-detector.sh "$1/cam_2" "$2/cam_2"

