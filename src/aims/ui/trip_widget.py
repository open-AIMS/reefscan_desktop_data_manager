from PyQt5 import QtCore, QtGui, QtWidgets, uic

from aims import state


class TripWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        ui_file = f'{state.meipass}resources/trip_widget.ui'
        uic.loadUi(ui_file, self)

    def load(self):
        self.edName.setText(state.model.trip["name"])
        self.edVessel.setText(state.model.trip["vessel"])
        self.edStart.setDate(state.model.trip["start_date"])
        self.edFinish.setDate(state.model.trip["finish_date"])

    def save(self):
        state.model.trip["name"] = self.edName.text()
        state.model.trip["vessel"] = self.edVessel.text()
        state.model.trip["start_date"] = self.edStart.date().toPyDate()
        state.model.trip["finish_date"] = self.edFinish.date().toPyDate()
        state.model.save_trip()

