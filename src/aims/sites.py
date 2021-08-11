from PyQt5 import uic
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QDialog, QMainWindow


class Sites(QDialog):
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

    def __init__(self, ui, model):
        super().__init__()
        self.model=model
        self.ui=uic.loadUi(ui, baseinstance=self)
        self.ui.tblSites.setModel(self.model.sitesModel)
        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)
        self.ui.tblSites.resizeColumnsToContents()

