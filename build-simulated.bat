pyinstaller -p src -p simulated_src --noconsole --name reefscan-simulated ^
    --add-data src\resources\*;resources ^
    --add-data src\fake_data\camera\a\*;fake_data\camera\a ^
    --add-data src\fake_data\camera\b\*;fake_data\camera\b ^
    --add-data src\fake_data\local\a\*;fake_data\local\a ^
    --add-data src\fake_data\local\b\*;fake_data\local\b ^
    --add-data src\fake_data\local\c\*;fake_data\local\c ^
    --add-data src\fake_data\camera\archive\a\*;fake_data\camera\archive\a ^
    --add-data src\fake_data\camera\archive\b\*;fake_data\camera\archive\b ^
    --icon src\resources\aims_fish.ico --onefile src\main.py