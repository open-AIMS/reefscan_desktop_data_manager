from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMainWindow


class TripDlg(QDialog):
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

    def __init__(self, ui, trip):
        super().__init__()
        self.ui=uic.loadUi(ui, baseinstance=self)
        self.trip = trip
        self.ui.edName.setText(trip["name"])
        self.ui.edVessel.setText(trip["vessel"])
        self.ui.edStart.setDate(trip["start_date"])
        self.ui.edFinish.setDate(trip["finish_date"])

        self.buttonBox.accepted.connect(self.ok)

        # self.ui.tblSites.setModel(self.basic_model.sitesModel)
    def ok(self):
        self.trip["name"] = self.ui.edName.text()
        self.trip["vessel"] = self.ui.edVessel.text()
        self.trip["start_date"] = self.ui.edStart.date().toPyDate()
        self.trip["finish_date"] = self.ui.edFinish.date().toPyDate()

