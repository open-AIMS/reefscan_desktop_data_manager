import logging
import os
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QTableView

from aims.aims_status_dialog import AimsStatusDialog
from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.gui_model.hardware_sync_model import HardwareSyncModel
from aims.operations.load_data_operation import LoadDataOperation
from aims.operations.load_hardware_sync_data_operation import LoadHardwareSyncDataOperation
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.operations.sync_to_server_operation import SyncToServerOperation
from aims.trip import TripDlg
from aims.widgets.combo_box_delegate import ComboBoxDelegate
from aims.sites import Sites
from aims.onboard_sync_dlg import OnboardSyncDlg
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.reader_writer import save_site
from aims.surveys_table import SurveysTable

logger = logging.getLogger(__name__)


class App(object):

    def __init__(self, meipass):
        # super().__init__(parent)
        self.sitesUi = f'{meipass}aims/sites.ui'
        self.tripUi = f'{meipass}aims/trip.ui'
        self.onboard_sync_ui = f'{meipass}aims/onboard_sync_dlg.ui'
        self.model = GuiModel()

        self.app = QtWidgets.QApplication(sys.argv)
        self.ui = uic.loadUi(f'{meipass}aims/app.ui')
        self.ui.setAttribute(Qt.WA_DeleteOnClose)

        self.config = Config(self.model)

        self.ui.btnOpenFolder.clicked.connect(self.open_data_folder)
        self.ui.btnLoadModel.clicked.connect(self.load_data)
        self.ui.actionSites.triggered.connect(self.edit_sites)
        self.ui.actionTrip.triggered.connect(self.edit_trip)
        self.ui.actionFrom_Aquisition_Hardware.triggered.connect(self.hardware_sync_prepare)
        self.ui.actionShow_Archives.triggered.connect(self.show_archives)
        self.ui.actionHardware_folder.triggered.connect(self.set_hardware_folder)
        self.ui.actionServer_Folder.triggered.connect(self.set_server_folder)
        self.ui.actionHardware_Archives.triggered.connect(self.hardware_archives)

        self.ui.actionTo_Reefscan.triggered.connect(self.sync_to_reefscan)
        self.surveys_table = SurveysTable(self.ui.tblSurveys, self.model.surveysModel,self.model)

        self.ui.showMaximized()
        self.ui.menubar.setVisible(False)

        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.onboard_sync_model = None

        self.app.exec()


    def load_data(self):
        logger.info("Load Data")
        self.model.set_data_folder(self.get_data_folder())
        operation = LoadDataOperation(self.model)
        operation.after_run.connect(self.load_model)
        self.aims_status_dialog.set_operation_connections(operation)
        self.aims_status_dialog.threadPool.apply_async(operation.run)

    def load_model(self):
        logger.info("load model")

        self.save_config_file()
        self.set_trip(self.model.get_trip_desc())
        self.ui.tblSurveys.viewport().update()
        self.model.surveysModel.layoutChanged.emit()
        self.ui.tblSurveys.setModel(self.model.surveysModel)

        self.ui.menubar.setVisible(True)
        self.aims_status_dialog.progress_dialog.close()

    def save_config_file(self):
        self.config.save_config_file(self.model)
        self.set_config_labels()

    def read_config_file(self):
        self.config.read_config_file(self.model)
        self.set_data_folder(self.config.data_folder)
        self.set_config_labels()

    def set_config_labels(self):
        self.ui.actionHardware_folder.setText(f"Hardware Folder ({self.model.hardware_data_folder})")
        self.ui.actionServer_Folder.setText(f"Server Folder ({self.model.server_data_folder})")

    def sync_to_reefscan(self):
        operation = SyncToServerOperation(self.model.data_folder, self.model.server_data_folder, False)
        self.aims_status_dialog.set_operation_connections(operation)
        operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        self.aims_status_dialog.threadPool.apply_async(operation.run)

    def show_archives(self):
        path = f"{self.model.data_folder}/archive"
        os.startfile(path)

    def hardware_archives(self):
        path = f"{self.model.hardware_data_folder}/archive"
        os.startfile(path)

    def hardware_sync_prepare(self):
        self.onboard_sync_model = self.model.make_onboard_sync_model()

        operation = LoadHardwareSyncDataOperation(self.onboard_sync_model)
        operation.after_run.connect(self.hardware_sync_show_dialog)
        self.aims_status_dialog.set_operation_connections(operation)
        self.aims_status_dialog.threadPool.apply_async(operation.run)

    def hardware_sync_show_dialog(self):
        onboard_dlg = OnboardSyncDlg(self.onboard_sync_ui, self.onboard_sync_model)
        onboard_dlg.setAttribute(Qt.WA_DeleteOnClose)
        onboard_dlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        result = onboard_dlg.exec()
        if result == QDialog.Accepted:
            self.update_from_hardware_model()

    def update_from_hardware_model(self):
        for site in self.onboard_sync_model.new_sites:
            site["folder"] = f"{self.model.data_folder}/sites/{site['uuid']}"
            save_site(site, self.model.sites_data_array)

        surveys_folder = f"{self.model.data_folder}/surveys"
        os.makedirs(surveys_folder, exist_ok=True)
        for survey in self.onboard_sync_model.data_array:
            survey_id = survey["id"]
            survey["folder"] = f"{surveys_folder}/{survey_id}"
            survey["trip"] = self.model.trip["uuid"]
            save_survey(survey)

        logger.info("set connections")
        operation = SyncFromHardwareOperation(self.onboard_sync_model.data_folder, self.model.data_folder)
        self.aims_status_dialog.set_operation_connections(operation)
        operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")

    def after_sync(self, args):
        message, detailed_message = args
        logger.info("after_hardware_sync")
        self.load_data()
        message_box = QtWidgets.QMessageBox()
        message_box.setText(message)
        message_box.setDetailedText(detailed_message)
        message_box.exec_()

    def edit_sites(self):
        try:
            sites = Sites(self.sitesUi, self.model)
            sites.setAttribute(Qt.WA_DeleteOnClose)
            sites.exec()
            self.model.make_sites_lookup()
            self.sitesComboBox.setChoices(self.model.surveysModel.sites_lookup)
        except Exception as e:
            print(e)

    def edit_trip(self):
        try:
            trip_dlg = TripDlg(self.tripUi, self.model.trip)
            trip_dlg.setAttribute(Qt.WA_DeleteOnClose)
            trip_dlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
            result = trip_dlg.exec()
            if result == QDialog.Accepted:
                self.model.make_trips_lookup()
                self.set_trip(self.model.get_trip_desc())
                self.model.save_trip()

        except Exception as e:
            print(e)

    def set_trip(self, trip):
        self.ui.lblTrip.setText(f'Trip: {trip}')

    def open_data_folder(self):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(self.model.data_folder)
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            self.set_data_folder(filename)

    def set_hardware_folder(self):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(self.model.hardware_data_folder)
        selected = filedialog.exec()

        if selected:
            folder = filedialog.selectedFiles()[0]
            self.model.hardware_data_folder = folder
            self.save_config_file()

    def set_server_folder(self):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(self.model.server_data_folder)
        selected = filedialog.exec()
        if selected:
            folder = filedialog.selectedFiles()[0]
            self.model.server_data_folder = folder
            self.save_config_file()

    def set_data_folder(self, filename):

        self.ui.edDataFolder.setText(filename)

    def get_data_folder(self):
        return self.ui.edDataFolder.text()
