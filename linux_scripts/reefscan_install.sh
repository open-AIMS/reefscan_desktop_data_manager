#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "  version  The version to install (e.g. v2.3.2)"
    exit 1
fi
version="$1"
cd
rm -r reefscan-data-manager-$version
tar xvfzp reefscan-data-manager-$version.tar
cd reefscan-data-manager-$version 
echo $version > reefscan_desktop_data_manager/src/resources/version.txt 
bash reefscan_desktop_data_manager/linux_scripts/setup.sh