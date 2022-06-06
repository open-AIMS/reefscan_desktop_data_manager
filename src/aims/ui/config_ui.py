import logging
import os
import sys
import time

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWizard, QCheckBox, QMessageBox

from aims import state
from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.ui.trip import TripDlg
from aims.operations.aims_status_dialog import AimsStatusDialog

logger = logging.getLogger(__name__)


class ConfigUi(object):
    def __init__(self):
        super().__init__()
        ui_file = f'{state.meipass}resources/config.ui'
        self.ui = uic.loadUi(ui_file)

        cb_slow_network: QCheckBox = self.ui.cbSlowNetwork
        cb_slow_network.setChecked(state.config.slow_network)

        self.ui.edLocal.setText(state.config.data_folder)
        self.ui.edBackup.setText(state.config.backup_data_folder)
        self.ui.edServer.setText(state.config.server_data_folder)

        self.ui.btnLocal.clicked.connect(self.local_clicked)
        self.ui.btnBackup.clicked.connect(self.backup_clicked)
        self.ui.btnServer.clicked.connect(self.server_clicked)

        self.ui.btn_next.clicked.connect(self.finished)
        self.aims_status_dialog = AimsStatusDialog(self.ui)

    def show(self):
        self.ui.show()

    def finished(self, page_id):
        logger.info("finished")
        state.config.data_folder = self.ui.edLocal.text()
        state.config.backup_data_folder = self.ui.edBackup.text()
        state.config.server_data_folder = self.ui.edServer.text()
        state.config.slow_network = self.ui.cbSlowNetwork.isChecked()

        state.config.save_config_file()

        state.load_data_model(aims_status_dialog=self.aims_status_dialog)

        if state.model.data_loaded:
            state.trip_dlg.show()
            self.ui.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(state.message)
            msg.setWindowTitle("Error")
            msg.exec_()

        logger.info("Really finished")

    def local_clicked(self):
        self.choose_file(self.ui.edLocal)

    def backup_clicked(self):
        self.choose_file(self.ui.edBackup)

    def server_clicked(self):
        self.choose_file(self.ui.edServer)

    def choose_file(self, edit_box):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(edit_box.text())
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            edit_box.setText(filename)

