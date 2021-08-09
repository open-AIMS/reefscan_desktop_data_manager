import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from abc import abstractmethod


class AimsAbstractTableModel(QtCore.QAbstractTableModel):

    data=[]
    columns = []
    editable = []

    datafolder = ""

    def data(self, index, role):
        if role == Qt.DisplayRole :
            try:
                rawValue = self.data[index.row()][self.columns[index.column()]]
                lookup = self.lookup(index.column())
                if lookup is None:
                    value = rawValue
                else:
                    value = lookup[rawValue]

            except Exception as e:
                value = ""
                traceback.print_exc()
            return str(value)

        if role == Qt.EditRole :
            try:
                rawValue = self.data[index.row()][self.columns[index.column()]]
                value = rawValue
            except Exception as e:
                value = ""
                traceback.print_exc()
            return str(value)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self.data[index.row()][self.columns[index.column()]] = value
            self.saveData(index.row())
            return True

    def rowCount(self, index):
        return len(self.data)

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
        if (self.editable[index.column()]):
            return  Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
        else:
            return  Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def readData(self, datafolder):
        pass

    def saveData(self, row):
        pass

    def lookup(self, column):
        return None
