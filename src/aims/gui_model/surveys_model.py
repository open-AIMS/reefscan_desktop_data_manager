from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import shortuuid
import os

from reefscanner.basic_model.reader_writer import save_survey
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class SurveysModel(AimsAbstractTableModel):
    columns = ["id", "project", "site", "", "transect", "depth", "trip", "start_date", "finish_date", "operator", "vessel", "folder",
               "photos", "start_lat", "start_lon",
               "finish_lat", "finish_lon"]
    editable = [False, True, True, False, True, True, False, False, False, True, True, False,
                False, False, False, False, False]
    sites_lookup = {}
    trips_lookup = {}
    projects_lookup = {}
    new_sites = []


    def data(self, index, role):
        if role == Qt.FontRole and index.column() in [3, 9]:
            font = QtGui.QFont()
            font.setUnderline(True)
            return font

        if role == Qt.ForegroundRole and index.column() in [3, 9]:
            return QtGui.QColor("blue")

        if role == Qt.DisplayRole and index.column() == 3:
            return "Make New Site"

        if role == Qt.DisplayRole and index.column() == 9:
            return "Open survey folder"

        return super().data(index, role)

    def save_data(self, row):
        survey = self.data_array[row]
        save_survey(survey)

    def set_hardware_data_folder(self, data_folder):
        if os.path.isdir(data_folder):
            self.hardware_data_folder = data_folder
            self.read_from_files()

    def clear_data(self):
        self.data_array = []

    def new_site_for_survey(self, row, site_name):
        site_id = shortuuid.uuid()
        survey = self.data_array[row]
        site = {"uuid": site_id, "name": site_name,
                "latitude": survey["start_lat"], "longitude": survey["start_lon"]
                }
        self.new_sites.append(site)
        self.sites_lookup[site_id] = site_name
        survey["site"] = site_id

    def lookup(self, column):
        if column == 1:
            return self.projects_lookup
        elif column == 2:
            return self.sites_lookup
        elif column == 6:
            return self.trips_lookup
        else:
            return None
