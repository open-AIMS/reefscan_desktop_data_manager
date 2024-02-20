python -V
python -m ensurepip
cd /mnt/reefscan
ls src
python -m pip install -r requirements.txt
/home/arch/.local/bin/pyinstaller --distpath macosdist -p src/ --noconsole --add-data src/resources/*:resources src/main.py
