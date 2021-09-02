import logging
import os
import time

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from aims.aims_status_dialog import AimsStatusDialog
from aims.config import Config
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.operations.load_data_operation import LoadDataOperation
from aims.operations.load_hardware_sync_data_operation import LoadHardwareSyncDataOperation

from aims.gui_model.model import GuiModel
from aims.surveys_table import SurveysTable

logger = logging.getLogger(__name__)


class EndOfDayWizard(object):
    def __init__(self, meipass):
        super().__init__()
        ui_file = f'{meipass}aims/end_of_day_wizard.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.wizardPageUploadFinished.setFinalPage(True)
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
        self.hardware_sync_model = None
        self.surveys_table = None

    def next_page(self, page_id):
        if page_id == 1:
            self.load_surveys_from_hardware()

        if page_id == 2:
            self.upload_from_hardware()

        if page_id == 3:
            self.load_all_surveys()

        print(page_id)
        print("next")

    def load_surveys_from_hardware(self):
        logger.info("Surveys before")
        self.load_model()
        self.hardware_sync_model = self.model.make_onboard_sync_model()
        operation = LoadHardwareSyncDataOperation(self.hardware_sync_model)
        self.aims_status_dialog.set_operation_connections(operation)
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()
        self.surveys_table = SurveysTable(self.ui.tblSurveysBefore, self.hardware_sync_model, None)

    def upload_from_hardware(self):
        operation = SyncFromHardwareOperation(self.model.hardware_data_folder, self.model.data_folder)
        self.aims_status_dialog.set_operation_connections(operation)
        # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()

    def load_all_surveys(self):
        self.load_model()
        self.ui.tblSurveysAfter.setModel(self.model.surveysModel)
        self.ui.tblSurveysAfter.resizeColumnsToContents()

    def load_model(self):
        logger.info("Surveys after")
        operation = LoadDataOperation(self.model)
        self.aims_status_dialog.set_operation_connections(operation)
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()
