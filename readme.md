#Initialise
`virtualenv venv`
`source venv/bin/activate`
or on windows
`venv\Scripts\Activate`
`python -m ensurepip`
`python -m pip install -r requirements.txt`


#Add dependencies
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

#Create executable  
pyinstaller -p src --noconsole --add-data src\resources\*;resources --onefile src\main.py