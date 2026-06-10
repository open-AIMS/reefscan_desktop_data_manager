#!/bin/bash

usage() {
	echo "Usage: $0 <input_dir> <output_dir>"
	echo
	echo "Runs COTS detection for one camera and copies the latest result to:"
	echo "  <output_dir>/final"
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
cd $REEFSCAN_HOME/ccip-cv-pipeline/cv-pipeline
source cv-pipeline-env/bin/activate

rm -r "$2/final"
python3 inference.py -p ../models/ccip-seg-nov24_ubuntu2004_x86_64/ccip-seg-nov24_ubuntu2004_x86_64.json -pp StoreProcessingResultPostProcessing -i "$1" -r "$2"

last_sub_folder=$(find "$2" -maxdepth 1 -mindepth 1 -type d | tail -n 1)

cp -r "$last_sub_folder" "$2/final"
