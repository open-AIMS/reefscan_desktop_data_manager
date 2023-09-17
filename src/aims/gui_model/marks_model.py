import logging

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
            self.data_frame:DataFrame = None
            print (e)

    def photo_file(self, r):
        return self.survey_folder + "/" + self.data_frame["file"][r]

    def photo_file_name(self, r):
        return self.data_frame["file"][r]


    def data(self, index: QModelIndex, role: int) -> any:
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            match col:
                case 0:
                    return self.data_frame["name"][row]
                case 1:
                    return self.data_frame["type"][row]
                case 2:
                    return self.data_frame["time"][row]
                case 3:
                    return str(self.data_frame["latitude"][row])
                case 4:
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

    def headerData(self, column, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            match column:
                case 0:
                    return "Name"
                case 1:
                    return "Type"
                case 2:
                    return "Time"
                case 3:
                    return "Latitude"
                case 4:
                    return "Longitude"
        return QVariant()

