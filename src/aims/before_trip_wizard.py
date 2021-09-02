import logging
import os
import time

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from aims.aims_status_dialog import AimsStatusDialog
from aims.config import Config
from aims.operations.sync_to_server_operation import SyncToServerOperation
from aims.operations.load_data_operation import LoadDataOperation
from aims.gui_model.model import GuiModel

logger = logging.getLogger(__name__)


class BeforeTripWizard(object):
    def __init__(self, meipass):
        super().__init__()
        ui_file = f'{meipass}aims/before_trip_wizard.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.wizardPageFinished.setFinalPage(True)
        self.ui.wizardPageSites.setFinalPage(True)
        self.ui.wizardPageProjects.setFinalPage(True)
        self.ui.currentIdChanged.connect(self.next_page)
        self.ui.setModal(True)
        logo_file = f'{meipass}icons/AIMSLogo_White_inline_250px.png'
        if os.path.exists(logo_file):
            logger.info("image exists")
        else:
            logger.info("image not found")

        self.ui.setPixmap(QtWidgets.QWizard.LogoPixmap, QPixmap(logo_file))
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.model = GuiModel()
        self.config = Config(self.model)

    def next_page(self, page_id):
        if page_id == 1:
            self.sync_to_reefscan()

        if page_id == 2:
            self.load_sites()

        if page_id == 3:
            self.load_projects()

        print(page_id)
        print("next")

    def load_sites(self):
        logger.info("Sites")
        operation = LoadDataOperation(self.model)
        self.aims_status_dialog.set_operation_connections(operation)
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()
        self.ui.tblSites.setModel(self.model.sitesModel)
        self.ui.tblSites.resizeColumnsToContents()

    def load_projects(self):
        self.ui.tblProjects.setModel(self.model.projects_model)
        self.ui.tblProjects.resizeColumnsToContents()

    def sync_to_reefscan(self):
        operation = SyncToServerOperation(self.model.data_folder, self.model.server_data_folder, True)
        self.aims_status_dialog.set_operation_connections(operation)
        # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()

