import logging
import os
import time

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWizard

from aims.config import Config
from aims.gui_model.model import GuiModel

logger = logging.getLogger(__name__)


class ConfigWizard(object):
    def __init__(self, meipass):
        super().__init__()
        ui_file = f'{meipass}aims/config.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.setModal(True)
        logo_file = f'{meipass}icons/AIMSLogo_White_inline_250px.png'
        self.ui.setPixmap(QtWidgets.QWizard.LogoPixmap, QPixmap(logo_file))
        self.model = GuiModel()
        self.config = Config(self.model)

        self.ui.edLocal.setText(self.model.data_folder)
        self.ui.edHardware.setText(self.model.hardware_data_folder)
        self.ui.edServer.setText(self.model.server_data_folder)

        self.ui.btnLocal.clicked.connect(self.local_clicked)
        self.ui.btnHardware.clicked.connect(self.hardware_clicked)
        self.ui.btnServer.clicked.connect(self.server_clicked)

        self.ui.button(QWizard.FinishButton).clicked.connect(self.finished)

    def finished(self, page_id):
        logger.info("finished")
        self.model.data_folder = self.ui.edLocal.text()
        self.model.hardware_data_folder = self.ui.edHardware.text()
        self.model.server_data_folder = self.ui.edServer.text()
        self.config.save_config_file(self.model)


    def local_clicked(self):
        self.choose_file(self.ui.edLocal)

    def server_clicked(self):
        self.choose_file(self.ui.edServer)

    def hardware_clicked(self):
        self.choose_file(self.ui.edHardware)

    def choose_file(self, edit_box):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(edit_box.text())
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            edit_box.setText(filename)

