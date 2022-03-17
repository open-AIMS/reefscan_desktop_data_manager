from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMainWindow, QVBoxLayout

from aims import state
from aims.gui_model.model import GuiModel

from aims.ui.trip_widget import TripWidget


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

    def __init__(self):

        super().__init__()
        self.ui = uic.loadUi(f'{state.meipass}resources/trip.ui')

        self.ui.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        vbox = QVBoxLayout()
        self.ui.groupBox.setLayout(vbox)
        self.trip_widget = TripWidget()
        vbox.addWidget(self.trip_widget)

        self.ui.buttonBox.accepted.connect(self.ok)

    def show(self):
        self.ui.show()
        self.trip_widget.load()

    def ok(self):
        self.trip_widget.save()
        state.surveys_tree.show()
