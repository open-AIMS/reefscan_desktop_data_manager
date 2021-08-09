#Initialise
install anaconda   
`conda create --name reef-scanner-data-entry --file conda_requirements.txt python=3.9`  
`conda activate --name reef-scanner-data-entry`

#Add dependencies  
`conda install <dependency name>`  
`conda list --export > conda_requirements.txt`

# Get all dependencies*  
`designerconda install --file conda_requirements.txt`    

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
pyinstaller -p src --noconsole --add-data src\aims\app.ui;aims --add-data src\aims\sites.ui;aims --onefile src\main.py