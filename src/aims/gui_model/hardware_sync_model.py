import os

import shortuuid
from PyQt5 import QtGui
from PyQt5.QtCore import Qt

from reefscanner.basic_model.exif_utils import get_exif_data
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class HardwareSyncModel(AimsAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.columns = ["id", "project", "site", "", "operator", "vessel", "photos",
                   "start_date", "start_lat", "start_lon",
                   "finish_date", "finish_lat", "finish_lon"]
        self.editable = [True, True, True, False, True, True, False, False, False, False, False]
        self.sites_lookup = {}
        self.projects_lookup = {}
        self.trips_lookup = {}
        self.trip = {}
        self.new_sites = []
        self.default_project = ""
        self.default_vessel = ""
        self.default_operator = ""

    def data(self, index, role):
        if role == Qt.FontRole and index.column() == 3:
            font = QtGui.QFont()
            font.setUnderline(True)
            return font

        if role == Qt.ForegroundRole and index.column() == 3:
            return QtGui.QColor("blue")

        if role == Qt.DisplayRole and index.column() == 3:
            return "Make New Site"

        return super().data(index, role)


    def set_hardware_data_folder(self, data_folder):
        if os.path.isdir(data_folder):
            self.hardware_data_folder = data_folder
            self.read_from_files()

    def clear_data(self):
        self.data_array = []

    def read_from_hardware_files(self):
        surveys_folder = f'{self.hardware_data_folder}/surveys'
        survey_folders = os.listdir(surveys_folder)
        for survey_folder in survey_folders:
            full_path = f'{surveys_folder}/{survey_folder}'
            survey_id = survey_folder
            photos = [name for name in os.listdir(full_path) if name.lower().endswith(".jpg")]
            photos.sort()
            count_photos = len(photos)
            if count_photos > 0:
                first_photo = f'{full_path}/{photos[0]}'
                (start_lat, start_lon, start_date) = get_exif_data(first_photo)
                last_photo = f'{full_path}/{photos[len(photos) - 1]}'
                (finish_lat, finish_lon, finish_date) = get_exif_data(last_photo)
                survey = {"id": survey_id, "name": survey_id, "photos": count_photos,
                          "start_date": start_date, "start_lat": start_lat, "start_lon": start_lon,
                          "finish_date": finish_date, "finish_lat": finish_lat, "finish_lon": finish_lon,
                          "site": "", "project": self.default_project, "operator": self.default_operator,
                          "vessel": self.default_vessel}
                self.data_array.append(survey)

    def new_site_for_survey(self, row, site_name):
        site_id = shortuuid.uuid()
        survey = self.data_array[row]
        site = {"uuid":site_id, "name": site_name,
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
        else:
            return None
