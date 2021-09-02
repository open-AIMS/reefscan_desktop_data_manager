import logging
import os

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWizard

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.config import Config
from aims.operations.sync_to_server_operation import SyncToServerOperation
from aims.operations.load_data_operation import LoadDataOperation
from aims.gui_model.model import GuiModel
from aims.ui.trip_widget import TripWidget

logger = logging.getLogger(__name__)


class BeforeTripWizard(object):
    def __init__(self, meipass):
        super().__init__()
        self.meipass = meipass
        ui_file = f'{meipass}resources/before_trip_wizard.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.wizardEditTrip.setFinalPage(True)
        self.ui.wizardPageSites.setFinalPage(True)
        self.ui.wizardPageProjects.setFinalPage(True)
        self.ui.currentIdChanged.connect(self.next_page)
        self.ui.setModal(True)
        logo_file = f'{meipass}resources/AIMSLogo_White_inline_250px.png'
        if os.path.exists(logo_file):
            logger.info("image exists")
        else:
            logger.info("image not found")

        self.ui.setPixmap(QtWidgets.QWizard.LogoPixmap, QPixmap(logo_file))
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.model = GuiModel()
        self.config = Config(self.model)
        self.trip_widget = None

    def next_page(self, page_id):
        if page_id == 1:
            self.sync_to_reefscan()

        if page_id == 2:
            self.load_trip()

        if page_id == 3:
            self.load_sites()

        if page_id == 4:
            self.load_projects()

        print(page_id)
        print("next")

    def load_trip(self):
        logger.info("Sites")
        operation = LoadDataOperation(self.model)
        self.aims_status_dialog.set_operation_connections(operation)
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()
        vbox = QVBoxLayout()
        self.ui.tripGroupBox.setLayout(vbox)
        self.trip_widget: TripWidget = TripWidget(self.meipass, self.model)
        vbox.addWidget(self.trip_widget)

        self.ui.button(QWizard.FinishButton).clicked.connect(self.finished)

    def finished(self, page_id):
        logger.info("finished")
        self.trip_widget.save()

    def load_sites(self):
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

