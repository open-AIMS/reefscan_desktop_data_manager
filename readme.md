# Initialise
`virtualenv venv`  

On Linux:  
`source venv/bin/activate`  
On Windows:  
`venv\Scripts\Activate`  

`python -m ensurepip`  
`python -m pip install -r requirements.txt`


# Add dependencies
add dependencies to requirements.txt

# GUI designer  
QT designer is installed as part of the PyQT depenency  
You can run it from a conda prompt  
`conda activate --name reef-scanner-data-entry`  
`designer`

You can integrate with Pycharm as an external tool (allows you to rightclick on a UI file and start the designer)  
First find the executable mine was here:  
`C:\ProgramData\Miniconda3\envs\reef-scanner-data-entry\Library\bin\designer`  
File - settings - external tools  
(+) to create  
These are the values for the three edit boxes  
1. C:\ProgramData\Miniconda3\envs\reef-scanner-data-entry\Library\bin\designer 
1. $FilePathRelativeToProjectRoot$
1. $ProjectFileDir$    

# Create executable  
On Windows:  
`pyinstaller -p src --noconsole --name reefscan-transom --add-data src\resources\*;resources --icon src\resources\aims_fish.ico --onefile src\main.py`
Rename the exe file to reefscan-deep.exe for reefscan deep functionality 
On Linux:  
`pyinstaller -p src --noconsole --name reefscan-transom --add-data src/resources/*:resources --icon src\resources\aims_fish.ico --onefile src/main.py`


pip install ..\reef_scanner_data_model\dist\reefscanner-0.2.0-py3-none-any.whl

# Language stuff
Create or update ts files
`pylupdate5 src/aims/ui/main_ui_components/data_component.py ^
src/resources/data.ui ^
src/resources/connect.ui ^
-ts src/resources/eng-backward.ts`

