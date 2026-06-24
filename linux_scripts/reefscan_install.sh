#!/bin/bash
version="v2.3.2"
cd
rm -r reefscan-data-manager-$version
tar xvfzp reefscan-data-manager-$version.tar
cd reefscan-data-manager-$version 
echo $version > reefscan_desktop_data_manager/src/resources/version.txt 
bash reefscan_desktop_data_manager/linux_scripts/setup.sh