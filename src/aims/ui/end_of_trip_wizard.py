import logging

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.config import Config
from aims.operations.sync_to_server_operation import SyncToServerOperation
from aims.gui_model.model import GuiModel

logger = logging.getLogger(__name__)


class EndOfTripWizard(object):
    def __init__(self, meipass):
        super().__init__()
        ui_file = f'{meipass}resources/end_of_trip_wizard.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.currentIdChanged.connect(self.next_page)
        self.ui.setModal(True)
        logo_file = f'{meipass}resources/AIMSLogo_White_inline_250px.png'
        self.ui.setPixmap(QtWidgets.QWizard.LogoPixmap, QPixmap(logo_file))
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.model = GuiModel()
        self.config = Config(self.model)

    def next_page(self, page_id):
        if page_id == 1:
            self.sync_to_reefscan()

    def sync_to_reefscan(self):
        operation = SyncToServerOperation(self.model.data_folder, self.model.server_data_folder, False)
        self.aims_status_dialog.set_operation_connections(operation)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()


