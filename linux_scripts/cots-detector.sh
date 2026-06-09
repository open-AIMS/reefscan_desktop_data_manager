#!/bin/bash
source ~/.reefscan_env
cd $REEFSCAN_HOME/ccip-cv-pipeline/cv-pipeline
source cv-pipeline-env/bin/activate

rm -r "$2/final"
python3 inference.py -p ../models/ccip-seg-nov24_ubuntu2004_x86_64/ccip-seg-nov24_ubuntu2004_x86_64.json -pp StoreProcessingResultPostProcessing -i "$1" -r "$2"

last_sub_folder=$(find "$2" -maxdepth 1 -mindepth 1 -type d | tail -n 1)

cp -r "$last_sub_folder" "$2/final"
