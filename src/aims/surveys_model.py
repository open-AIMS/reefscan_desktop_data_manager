from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import os
from aims.json_utils import read_json_file
from aims.json_utils import write_json_file
from aims.widgets.aims_abstract_table_model import AimsAbstractTableModel


class SurveysModel(AimsAbstractTableModel):
    columns = ["name", "project", "site", "trip", "start_date", "finish_date", "operator", "vessel", "folder"]
    editable = [True, True, True, False, False, False, True, True, False]
    sites_lookup = {}
    trips_lookup = {}
    projects_lookup = {}

    def data(self, index, role):
        if role == Qt.FontRole and index.column() == 8:
            font = QtGui.QFont()
            font.setUnderline(True)
            return font

        if role == Qt.ForegroundRole and index.column() == 8:
            return QtGui.QColor("blue")

        if role == Qt.DisplayRole and index.column() == 8:
            return "Open survey folder"

        return super().data(index, role)

    def save_data(self, row):
        survey = self.data[row]
        self.save_survey(survey)

    def save_survey(self, survey):
        survey_to_save = survey.copy()
        folder = survey_to_save.pop('folder')
        write_json_file(folder, 'survey.json', survey_to_save)

    def read_data(self, datafolder):
        self.datafolder = datafolder
        self.data_array = []
        surveys_folder = f'{self.datafolder}/surveys'
        survey_folders = os.listdir(surveys_folder)
        for survey_folder in survey_folders:
            fullPath = f'{surveys_folder}/{survey_folder}'
            if os.path.isdir(fullPath):
                print(survey_folder)
                survey_file = f'{fullPath}/survey.json'
                survey = read_json_file(survey_file)
                survey["folder"] = fullPath
                self.data_array.append(survey)

    def lookup(self, column):
        if column == 1:
            return self.projects_lookup
        elif column == 2:
            return self.sites_lookup
        elif column == 3:
            return self.trips_lookup
        else:
            return None
