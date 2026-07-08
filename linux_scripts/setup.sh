REEFSCAN_HOME="$(pwd)"
COTS_HOME="$HOME/reefscan-cots-model"

# when you start a script by double clicking it, 
# it doesn't have the environment variables set in .bashrc
# also .bashrc has  guard preventing it from running in non-interactive shells, 
# so we source ~/.reefscan_env which is created by this setup script 
# and contains the necessary environment variables

echo "REEFSCAN_HOME=\"$REEFSCAN_HOME\"" > ~/.reefscan_env
echo "COTS_HOME=\"$COTS_HOME\"" >> ~/.reefscan_env


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

