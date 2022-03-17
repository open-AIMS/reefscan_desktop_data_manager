from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QComboBox

from aims import state
from aims.ui.methods import Methods


class TripWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        ui_file = f'{state.meipass}resources/trip_widget.ui'
        uic.loadUi(ui_file, self)
        self.btnAddMethod.clicked.connect(self.add_method)
        self.open_dlg = None
        self.cb_project: QComboBox = self.cbProject
        self.cb_method: QComboBox = self.cbMethod

    def add_method(self):
        print("Add Method")
        self.open_dlg = Methods()
        self.open_dlg.show()

    def load(self):
        self.edName.setText(state.model.trip["name"])
        self.edVessel.setText(state.model.trip["vessel"])
        self.edStart.setDate(state.model.trip["start_date"])
        self.edFinish.setDate(state.model.trip["finish_date"])
        self.project_lookup()
        self.method_lookup()

    def save(self):
        state.model.trip["name"] = self.edName.text()
        state.model.trip["vessel"] = self.edVessel.text()
        state.model.trip["start_date"] = self.edStart.date().toPyDate()
        state.model.trip["finish_date"] = self.edFinish.date().toPyDate()
        state.model.trip["method"] = self.cb_method.currentData()
        state.model.trip["project"] = self.cb_project.currentData()
        state.model.save_trip()

    def project_lookup(self):
        lookup = state.model.surveysModel.projects_lookup.items()
        for key, value in sorted(lookup, key=lambda item: item[1]):
            self.cb_project.addItem(value, key)
        if "project" in state.model.trip:
            project_ = state.model.trip["project"]
            self.cb_project.setCurrentIndex(self.cb_project.findData(project_))

    def method_lookup(self):
        lookup = state.model.surveysModel.method_lookup.items()
        for key, value in sorted(lookup, key=lambda item: item[1]):
            self.cb_method.addItem(value, key)
        if "method" in state.model.trip:
            method_ = state.model.trip["method"]
            self.cb_method.setCurrentIndex(self.cb_method.findData(method_))
