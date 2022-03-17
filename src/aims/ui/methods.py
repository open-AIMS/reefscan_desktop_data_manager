import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QModelIndex, QItemSelection

from PyQt5.QtWidgets import QDialog, QMainWindow, QTableView, QTextEdit
from aims import state
class Methods:
    # done_signal = pyqtSignal(str)

    # def __init__(self, displaytext):
    #     super().__init__()
    #
    #     self.setWindowModality(QtCore.Qt.ApplicationModal)
    #     self.disp = displaytext
    #     self.ui = dialog_window.Ui_Dialog()
    #
    # self.ui.setupUi(self)
    #
    # self.ui.label_message.setText(self.disp)

    def __init__(self):
        super().__init__()
        self.model = state.model
        self.ui = uic.loadUi(f'{state.meipass}resources/methods.ui')
        self.ui.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.ui.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        self.tbl_methods: QTableView = self.ui.tblMethods
        self.tbl_methods.setModel(self.model.methodsModel)
        self.tbl_methods.resizeColumnsToContents()
        self.ui.btnAdd.clicked.connect(self.add_row)
        self.ui.btnDelete.clicked.connect(self.delete_row)
        self.tbl_methods.selectionModel().selectionChanged.connect(self.selection_changed)

    def selection_changed(self, selected: QItemSelection, deselected: QItemSelection):

        ed_description: QTextEdit = self.ui.edDescription
        if len(deselected.indexes()) == 1:
            deselected_row = deselected.indexes()[0].row()
            deselected_item = self.model.methods_data_array[deselected_row]
            deselected_item["description"] = ed_description.toPlainText()
            self.model.methodsModel.save_data(deselected_row)

        if len(selected.indexes()) == 1:
            selected_row = selected.indexes()[0].row()
            selected_item = self.model.methods_data_array[selected_row]
            ed_description.setText(selected_item["description"])


    def show(self):
        self.ui.show()

    def add_row(self):
        print("add")
        index = self.model.methodsModel.index(0, 0)
        print(index)
        self.model.methodsModel.insertRows(index.row(), 1, index, None)

    def delete_row(self):
        index = self.tbl_methods.currentIndex()
        selected_row = index.row()
        selected_item = self.model.methods_data_array[selected_row]
        if "folder" in selected_item:
            folder = selected_item["folder"]
            file = folder + "/method.json"
            os.remove(file)
            os.removedirs(folder)
        self.model.methodsModel.removeRows(selected_row, 1, index)




