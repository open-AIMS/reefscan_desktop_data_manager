from PyQt5 import QtCore, QtGui, QtWidgets, uic


class TripWidget(QtWidgets.QWidget):
    def __init__(self, meipass, model):
        super().__init__()
        ui_file = f'{meipass}resources/trip_widget.ui'
        uic.loadUi(ui_file, self)
        self.model = model

        self.edName.setText(model.trip["name"])
        self.edVessel.setText(model.trip["vessel"])
        self.edStart.setDate(model.trip["start_date"])
        self.edFinish.setDate(model.trip["finish_date"])

    def save(self):
        self.model.trip["name"] = self.edName.text()
        self.model.trip["vessel"] = self.edVessel.text()
        self.model.trip["start_date"] = self.edStart.date().toPyDate()
        self.model.trip["finish_date"] = self.edFinish.date().toPyDate()
        self.model.save_trip()

