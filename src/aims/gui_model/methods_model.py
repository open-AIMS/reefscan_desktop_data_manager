import logging
import os

import shortuuid
from reefscanner.basic_model.reader_writer import save_method

from aims import state
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel

logger = logging.getLogger(__name__)


class MethodsModel(AimsAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.columns = ["name", "description"]
        self.editable = [True, False]

    def save_data(self, row):
        method = self.data_array[row]
        if "uuid" not in method:
            uuid = shortuuid.uuid()
            method["uuid"] = uuid
            folder = state.model.data_folder + "/methods/" + uuid
            os.makedirs(folder)
            method["folder"] = folder

        save_method(method, self.data_array)

    def insertRows(self, position, rows, QModelIndex, parent):
        self.beginInsertRows(QModelIndex, position, position + rows - 1)
        default_row = {"name": "method_name", "description": "method_description"}
        for i in range(rows):
            self.data_array.insert(position, default_row)
        self.endInsertRows()
        self.layoutChanged.emit()
        return True

    def removeRows(self, position, rows, QModelIndex):
        self.beginRemoveRows(QModelIndex, position, position + rows - 1)
        for i in range(rows):
            del (self.data_array[position])
        self.endRemoveRows()
        self.layoutChanged.emit()
        return True
