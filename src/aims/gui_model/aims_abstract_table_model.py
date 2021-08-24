import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from abc import abstractmethod


class AimsAbstractTableModel(QtCore.QAbstractTableModel):
    data_array = []
    columns = []
    editable = []
    auto_save = True

    data_folder = ""

    def data(self, index, role):
        row_ = self.data_array[index.row()]
        column_name = self.columns[index.column()]
        if role == Qt.DisplayRole:
            try:
                if column_name in row_:
                    rawValue = row_[column_name]
                    lookup = self.lookup(index.column())
                    if lookup is None or rawValue == "":
                        value = rawValue
                    else:
                        value = lookup[rawValue]
                else:
                    value = ""

            except Exception as e:
                value = ""
                traceback.print_exc()
            return str(value)

        if role == Qt.EditRole:
            try:
                rawValue = row_[column_name]
                value = rawValue
            except Exception as e:
                value = ""
                traceback.print_exc()
            return str(value)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self.data_array[index.row()][self.columns[index.column()]] = value
            if self.auto_save:
                self.save_data(index.row())
            return True

    def rowCount(self, index):
        return len(self.data_array)

    def columnCount(self, index):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.columns[section])

            if orientation == Qt.Vertical:
                return ""

    def flags(self, index):
        if self.is_editable(index):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def is_editable(self, index):
        try:
            return self.editable[index.column()]
        except:
            return False

    def read_data(self, datafolder):
        pass

    def save_data(self, row):
        pass

    def lookup(self, column):
        return None
