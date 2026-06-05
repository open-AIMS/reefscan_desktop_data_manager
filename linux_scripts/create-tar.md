The zip should be created for a specific tag I will use v2.3.2 as an example

Do this in bash
```
# the next two lines are for windows subsystem for linux
sudo mkdir /mnt/pearl_techdev
sudo mount -t drvfs '\\pearl\techdev' /mnt/pearl_techdev
mkdir reefscan-data-manager-v2_3_2
cd reefscan-data-manager-v2_3_2
cp /mnt/pearl_techdev/Software/ccip/20241127ccip-cv-pipeline.zip .
unzip 20241127ccip-cv-pipeline.zip
rm 20241127ccip-cv-pipeline.zip
git clone --depth 1 --branch v2.3.2 https://github.com/open-AIMS/reefscan_desktop_data_manager
rm -r reefscan_desktop_data_manager/.git
rm -r reefscan_desktop_data_manager/.github
rm -r ccip-cv-pipeline/datasets
# the following line makes all files in this folder and subfolders readable and wratable
# and all folders executable as well
chmod -R a+rw . && find . -type d -exec chmod +x {} +
cd ..
tar cvfzp reefscan-data-manager-v2_3_2.tar reefscan-data-manager-v2_3_2
```
modify install.sh to point to tis tar file

