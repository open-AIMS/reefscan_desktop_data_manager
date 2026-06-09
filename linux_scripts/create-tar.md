The zip should be created for a specific tag I will use v2.3.2 as an example

Do this in bash
```
# the next two lines are for windows subsystem for linux
sudo mkdir /mnt/pearl_techdev
sudo mount -t drvfs '\\pearl\techdev' /mnt/pearl_techdev
mkdir reefscan-data-manager-60eod
cd reefscan-data-manager-60eod
cp /mnt/pearl_techdev/Software/ccip/20241127ccip-cv-pipeline.zip .
unzip 20241127ccip-cv-pipeline.zip
rm 20241127ccip-cv-pipeline.zip
mv 20241127ccip-cv-pipeline/ccip-cv-pipeline/ .
rmdir 20241127ccip-cv-pipeline
git clone --depth 1 --branch feature/60_end_of_day https://github.com/open-AIMS/reefscan_desktop_data_manager
sudo rm -r reefscan_desktop_data_manager/.git
sudo rm -r reefscan_desktop_data_manager/.github
sudo rm -r ccip-cv-pipeline/datasets
# the following line makes all files in this folder and subfolders readable and writable
# and all folders executable as well
chmod -R a+rw . && find . -type d -exec chmod +x {} + && find . -name "*.sh" -exec chmod +x {} +
cd ..
tar cvfzp reefscan-data-manager-60eod.tar reefscan-data-manager-60eod

```
modify install.sh to point to tis tar file

