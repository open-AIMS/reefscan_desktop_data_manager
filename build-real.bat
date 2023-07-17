pyinstaller -p src -p real_src --noconsole --name reefscan-transom ^
    --add-data src\resources\*;resources ^
    --icon src\resources\aims_fish.ico --onefile src\main.py