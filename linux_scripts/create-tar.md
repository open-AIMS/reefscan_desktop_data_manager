The zip should be created for a specific tag or branch I will use v2.3.3 as an example

Do this in bash
```
# the next two lines are for windows subsystem for linux
mkdir reefscan-data-manager-v2_3_3
cd reefscan-data-manager-v2_3_3
git clone --depth 1 --branch v2.3.3 https://github.com/open-AIMS/reefscan_desktop_data_manager
sudo rm -r reefscan_desktop_data_manager/.git
sudo rm -r reefscan_desktop_data_manager/.github
# the following line makes all files in this folder and subfolders readable and writable
# and all folders executable as well
chmod -R a+rw . && find . -type d -exec chmod +x {} + && find . -name "*.sh" -exec chmod +x {} +
cd ..
tar cvfzp reefscan-data-manager-v2_3_3.tar reefscan-data-manager-v2_3_3

```
to install run

```
reefscan_install.sh v2_3_3
```
