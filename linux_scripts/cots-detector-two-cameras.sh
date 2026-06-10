#!/bin/bash

usage() {
	echo "Usage: $0 <input_root> <output_root>"
	echo
	echo "Runs COTS detection for both cameras using:"
	echo "  <input_root>/cam_1 -> <output_root>/cam_1"
	echo "  <input_root>/cam_2 -> <output_root>/cam_2"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
	usage
	exit 0
fi

if [ "$#" -ne 2 ]; then
	usage >&2
	exit 1
fi

source ~/.reefscan_env
 
$REEFSCAN_HOME/reefscan_desktop_data_manager/linux_scripts/cots-detector.sh "$1/cam_1" "$2/cam_1"
$REEFSCAN_HOME/reefscan_desktop_data_manager/linux_scripts/cots-detector.sh "$1/cam_2" "$2/cam_2"

