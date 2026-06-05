REEFSCAN_HOME="$(pwd)"

# when you start a script by double clicking it, 
# it doesn't have the environment variables set in .bashrc
# also .bashrc has  guard preventing it from running in non-interactive shells, 
# so we source ~/.reefscan_env which is created by this setup script 
# and contains the necessary environment variables

echo "REEFSCAN_HOME=\"$REEFSCAN_HOME\"" > ~/.reefscan_env
echo "PATH=/usr/local/cuda/bin${PATH:+:${PATH}}" >> ~/.reefscan_env
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/reefscan/tensorrt/TensorRT-8.6.1.6/lib" >> ~/.reefscan_env

if ! command -v python3.8 &> /dev/null; then
    sudo apt update && sudo apt install software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update && sudo apt install python3.8 python3.8-venv
fi


cd $REEFSCAN_HOME/reefscan_desktop_data_manager
python3.8 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-eod.txt 
cp linux_scripts/reefscan-deep.desktop ~/Desktop
cp linux_scripts/reefscan-transom.desktop ~/Desktop
cp linux_scripts/reefscan-deep.sh ~/Desktop
cp linux_scripts/reefscan-transom.sh ~/Desktop

cd $REEFSCAN_HOME/ccip-cv-pipeline/cv-pipeline

python3.8 configure_project.py -a
python3.8 build_venv.py
source cv-pipeline-env/bin/activate

