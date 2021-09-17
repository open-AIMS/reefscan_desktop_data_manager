python --version
python -m ensurepip
cd /mnt/reefscan
python -m pip install -r requirements.txt
/home/arch/.local/bin/pyinstaller --distpath macosdist -p src/ --noconsole --add-data src/resources/*:resources src/main.py/
