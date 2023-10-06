#!/bin/bash
cd ~/ccip-cv-pipeline/cv-pipeline/
source cv-pipeline-env/bin/activate

python3 inference.py -p ../models/ccip-deploy-mar23-1344x768_ubuntu_x86_64/ccip-deploy-mar23-1344x768_ubuntu_x86_64.json -pp StoreProcessingResultPostProcessing -i "$1" -r "$2"

last_sub_folder=$(find $2 -maxdepth 1 -mindepth 1 -type d | tail -n 1)

mv $last_sub_folder $2/final
