from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import os
from aims.utils import readJsonFile
from aims.utils import writeJsonFile
from aims.widgets.aims_abstract_table_model import AimsAbstractTableModel

class SurveysModel(AimsAbstractTableModel):

    columns = ["name", "project", "site","trip", "start_date", "finish_date", "operator", "vessel", "folder"]
    editable = [True, True, True, False, False, False, True, True, False]
    sites_lookup = {}
    trips_lookup = {}
    projects_lookup = {}

    def data(self, index, role):
        if role == Qt.FontRole and index.column()==8:
            font = QtGui.QFont()
            font.setUnderline(True)
            return font

        if role == Qt.ForegroundRole and index.column()==8:
            return QtGui.QColor("blue")

        if role == Qt.DisplayRole and index.column()==8:
            return "Open survey folder"

        return super().data(index, role)


    def saveData(self, row):
        survey = self.data[row].copy()
        folder = survey.pop('folder')
        writeJsonFile(f'{folder}/survey.json', survey)


    def readData(self, datafolder):
        self.datafolder = datafolder
        self.data=[]
        surveysFolder = f'{self.datafolder}/surveys'
        surveyFolders = os.listdir(surveysFolder)
        for surveyFolder in surveyFolders:
            fullPath = f'{surveysFolder}/{surveyFolder}'
            if os.path.isdir(fullPath):
                print(surveyFolder)
                surveyFile = f'{fullPath}/survey.json'
                survey = readJsonFile(surveyFile)
                survey["folder"] = fullPath
                self.data.append(survey)

    def lookup(self, column):
        if (column == 1):
            return self.projects_lookup
        elif (column == 2):
            return self.sites_lookup
        elif (column == 3):
            return self.trips_lookup
        else:
            return None