import os
import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QProgressDialog
from reefscanner.basic_model.reader_writer import save_site
from aims.gui_model.model import GuiModel
from aims.operations.load_data_operation import LoadDataOperation
from aims.gui_model.surveys_model import SurveysModel
from aims.trip import TripDlg
from aims.widgets.combo_box_delegate import ComboBoxDelegate
from aims.sites import Sites
from aims.sync.sync_to_reefscan_server import sync_to_reefscan_server
from aims.sync.sync_from_hardware import sync_from_hardware
from aims.onboard_sync_dlg import OnboardSyncDlg
from reefscanner.basic_model.json_utils import write_json_file
from reefscanner.basic_model.json_utils import read_json_file


# class App(QtWidgets.QMainWindow):
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
        try:
            data_folder_json = read_json_file("c:/aims/reef-scanner/config.json")
            self.set_data_folder(data_folder_json["data_folder"])
        except:
            self.set_data_folder("c:/aims/reef-scanner")

        self.ui.btnOpenFolder.clicked.connect(self.open_data_folder)
        self.ui.btnLoadModel.clicked.connect(self.load_data)
        self.ui.actionSites.triggered.connect(self.edit_sites)
        self.ui.actionTrip.triggered.connect(self.edit_trip)
        self.ui.actionFrom_Aquisition_Hardware.triggered.connect(self.onboard_sync)
        self.ui.actionShow_Archives.triggered.connect(self.show_archives)

        self.ui.actionTo_Reefscan.triggered.connect(self.sync_to_reefscan)
        # self.ui.tblSurveys.setModel(self.basic_model.surveysModel)
        self.ui.tblSurveys.setEditTriggers(
            QAbstractItemView.SelectedClicked | QAbstractItemView.AnyKeyPressed | QAbstractItemView.DoubleClicked)
        self.ui.tblSurveys.clicked.connect(self.table_clicked)
        self.projectsComboBox = ComboBoxDelegate(self.model.surveysModel.projects_lookup)
        self.ui.tblSurveys.setItemDelegateForColumn(1, self.projectsComboBox)
        self.sitesComboBox = ComboBoxDelegate(self.model.surveysModel.sites_lookup)
        self.ui.tblSurveys.setItemDelegateForColumn(2, self.sitesComboBox)
        self.ui.tblSurveys.resizeColumnsToContents()
        self.ui.showMaximized()

        self.app.exec()

    def load_data(self):
        self.model.set_data_folder(self.get_data_folder())

        progress_dialog = QProgressDialog("Loading data.", None,0, 10, self.ui)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setWindowModality(Qt.WindowModal);
        load_data_operation = LoadDataOperation(self.model, progress_dialog, self.load_model)
        QThreadPool.globalInstance().start(load_data_operation)

    def load_model(self):
        data_folder_json = {"data_folder": self.get_data_folder()}
        write_json_file("c:/aims/reef-scanner", "config.json", data_folder_json)
        self.set_trip(self.model.get_trip_desc())
        self.ui.tblSurveys.viewport().update()
        self.model.surveysModel.layoutChanged.emit()
        self.ui.tblSurveys.setModel(self.model.surveysModel)
        self.sitesComboBox.setChoices(self.model.surveysModel.sites_lookup)
        self.projectsComboBox.setChoices(self.model.surveysModel.projects_lookup)


    def sync_to_reefscan(self):
        (message, detailed_message) = sync_to_reefscan_server(self.model.data_folder)
        print("finished copying")
        message_box = QtWidgets.QMessageBox()
        message_box.setText(message)
        message_box.setDetailedText(detailed_message)
        message_box.exec_()
        self.load_model()

    def show_archives(self):
        path = f"{self.model.data_folder}/archive"
        os.startfile(path)

    def table_clicked(self, index):
        if index.column() == 9:
            path = self.model.surveysModel.data_array[index.row()]["folder"]
            os.startfile(path)
        if index.column() == 3:
            self.make_site(index)

    def make_site(self, index):
        input_box = QtWidgets.QInputDialog()
        input_box.setLabelText("Site Name")
        result = input_box.exec_()
        if result == QDialog.Accepted:
            site_name = input_box.textValue()
            self.model.surveysModel.new_site_for_survey(index.row(), site_name)
            self.sitesComboBox.setChoices(self.model.surveysModel.sites_lookup)

            for site in self.model.surveysModel.new_sites:
                site["folder"] = f"{self.model.data_folder}/sites/{site['uuid']}"
                save_site(site, self.model.sites_data_array)

            self.model.surveysModel.save_data(index.row())

        self.model.surveysModel.new_sites = []

    def onboard_sync(self):
        onboard_sync_model = SurveysModel()
        onboard_sync_model.sites_lookup = self.model.surveysModel.sites_lookup.copy()
        onboard_sync_model.projects_lookup = self.model.surveysModel.projects_lookup
        onboard_sync_model.trips_lookup = self.model.surveysModel.trips_lookup
        onboard_sync_model.default_project = self.model.default_project
        onboard_sync_model.trip = self.model.trip
        onboard_sync_model.auto_save = False
        surveys = self.model.surveysModel.data_array
        onboard_sync_model.default_operator = surveys[len(surveys) - 1]["operator"]
        onboard_sync_model.read_data("C:/aims/reef-scanner/ONBOARD", self.model.trip)

        onboard_dlg = OnboardSyncDlg(self.onboard_sync_ui, onboard_sync_model)
        onboard_dlg.setAttribute(Qt.WA_DeleteOnClose)
        onboard_dlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        result = onboard_dlg.exec()
        if result == QDialog.Accepted:
            self.update_from_hardware(onboard_dlg.model, surveys)

    def update_from_hardware(self, onboard_model, surveys):
        for site in onboard_model.new_sites:
            site["folder"] = f"{self.model.data_folder}/sites/{site['uuid']}"
            self.model.sitesModel.save_site(site)

        for survey in onboard_model.data_array:
            survey_id = survey["id"]
            survey["folder"] = f"{self.model.data_folder}/surveys/{survey_id}"
            survey["trip"] = self.model.trip["uuid"]
            self.model.surveysModel.save_survey(survey)

        self.model.surveysModel.beginResetModel()
        self.model.sitesModel.data_array = self.model.sitesModel.data_array + onboard_model.new_sites
        self.model.surveysModel.data_array = surveys + onboard_model.data_array
        self.model.surveysModel.endResetModel()
        self.model.make_sites_lookup()
        self.sitesComboBox.setChoices(self.model.surveysModel.sites_lookup)
        sync_from_hardware(onboard_model.data_folder, self.model.data_folder)

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

    def set_data_folder(self, filename):
        self.ui.edDataFolder.setText(filename)

    def get_data_folder(self):
        return self.ui.edDataFolder.text()

