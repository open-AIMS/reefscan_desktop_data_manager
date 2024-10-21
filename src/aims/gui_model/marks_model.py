import logging
from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex, QVariant
import pandas as pd
from pandas import DataFrame

logger = logging.getLogger("")


class MarksModel(QtCore.QAbstractTableModel):
    def __init__(self, survey_folder):
        self.survey_folder = survey_folder
        super().__init__()
        try:
            self.data_frame = pd.read_csv(survey_folder + "/" + "marks.csv")
        except Exception as e:
            self.data_frame: DataFrame = None
            print(e)

    def photo_file(self, r):
        return self.survey_folder + "/" + self.photo_file_name(r)

    def photo_file_name(self, r):
        full_file_name = self.data_frame["file"][r]
        (dir, filename) = path.split(full_file_name)
        (dir, camera_dir) = path.split(dir)
        return f"{camera_dir}/{filename}"

    def data(self, index: QModelIndex, role: int) -> any:
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return self.data_frame["name"][row]
            elif col == 1:
                return self.data_frame["type"][row]
            elif col == 2:
                return self.data_frame["time"][row]
            elif col == 3:
                return str(self.data_frame["latitude"][row])
            elif col == 4:
                return str(self.data_frame["longitude"][row])
        return QVariant()

    def hasData(self):
        return self.data_frame is not None and not self.data_frame.empty

    def rowCount(self, index):
        if self.data_frame is None:
            return 0
        else:
            cnt = self.data_frame.shape[0]
            return cnt

    def columnCount(self, index):
        return 5

    def flags(self, index):
        return Qt.ItemIsEnabled

    def headerData(self, col, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if col == 0:
                return "Name"
            elif col == 1:
                return "Type"
            elif col == 2:
                return "Time"
            elif col == 3:
                return "Latitude"
            elif col == 4:
                return "Longitude"
        return QVariant()
