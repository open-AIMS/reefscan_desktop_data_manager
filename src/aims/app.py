import os
import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QDialog

from aims.onbard_sync_model import OnboardSyncModel
from aims.trip import TripDlg
from aims.widgets.combo_box_delegate import ComboBoxDelegate
from aims.sites import Sites
from aims.sync.sync_to_reefscan_server import sync_to_reefscan_server
from aims.sync.sync_from_hardware import sync_from_hardware
from aims.onboard_sync_dlg import OnboardSyncDlg

from aims.model import Model


# class App(QtWidgets.QMainWindow):
class App(object):

    def __init__(self, meipass):
        # super().__init__(parent)
        self.sitesUi = f'{meipass}aims/sites.ui'
        self.tripUi = f'{meipass}aims/trip.ui'
        self.onboard_sync_ui = f'{meipass}aims/onboard_sync_dlg.ui'
        self.model = Model()
        self.model.set_data_folder("c:/aims/reef-scanner")
        self.app = QtWidgets.QApplication(sys.argv)
        # self.ui=uic.loadUi(ui, baseinstance=self)
        self.ui = uic.loadUi(f'{meipass}aims/app.ui')
        self.ui.setAttribute(Qt.WA_DeleteOnClose)
        self.load_model()
        self.ui.btnOpenFolder.clicked.connect(self.open_data_folder)
        self.ui.edDataFolder.textChanged.connect(self.data_folder_changed)
        self.ui.actionSites.triggered.connect(self.edit_sites)
        self.ui.actionTrip.triggered.connect(self.edit_trip)
        self.ui.actionFrom_Aquisition_Hardware.triggered.connect(self.onboard_sync)
        self.ui.actionShow_Archives.triggered.connect(self.show_archives)

        self.ui.actionTo_Reefscan.triggered.connect(self.sync_to_reefscan)
        self.ui.tblSurveys.setModel(self.model.surveysModel)
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
        if index.column() == 8:
            try:
                path = self.model.surveysModel.data_array[index.row()]["folder"]
                print(path)
                os.startfile(path)
            except Exception as e:
                print(e)

    def onboard_sync(self):
        try:
            onboard_sync_model = OnboardSyncModel()
            onboard_sync_model.sites_lookup = self.model.surveysModel.sites_lookup.copy()
            onboard_sync_model.projects_lookup = self.model.surveysModel.projects_lookup
            onboard_sync_model.default_project = self.model.default_project
            onboard_sync_model.default_vessel = self.model.trip["vessel"]
            surveys = self.model.surveysModel.data_array
            onboard_sync_model.default_operator = surveys[len(surveys)-1]["operator"]
            onboard_sync_model.set_data_folder("C:/aims/reef-scanner/ONBOARD")

            onboard_dlg = OnboardSyncDlg(self.onboard_sync_ui, onboard_sync_model)
            onboard_dlg.setAttribute(Qt.WA_DeleteOnClose)
            onboard_dlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
            result = onboard_dlg.exec()
            if result == QDialog.Accepted:

                self.update_from_hardware(onboard_dlg.model, surveys)

        except Exception as e:
            print(e)

    def update_from_hardware(self, onboard_model, surveys):
        for site in onboard_model.new_sites:
            site["folder"] = f"{self.model.data_folder}/sites/{site['uuid']}"
            self.model.sitesModel.save_site(site)

        for survey in onboard_model.data_array:
            survey_id = survey.pop("id")
            survey.pop("start_lat")
            survey.pop("start_lon")
            survey.pop("finish_lat")
            survey.pop("finish_lon")
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
            print(result)
            if result == QDialog.Accepted:
                print(self.model.trip)
                self.model.makeTripsLookup()
                self.set_trip(self.model.getTripDesc())
                self.model.saveTrip()

        except Exception as e:
            print(e)

    def load_model(self):
        print("loading model")
        self.set_data_folder(self.model.data_folder)
        self.set_trip(self.model.getTripDesc())

    def set_trip(self, trip):
        self.ui.lblTrip.setText(f'Trip: {trip}')

    def open_data_folder(self):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(self.model.data_folder)
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            print(filename)
            self.set_data_folder(filename)

    def set_data_folder(self, filename):
        self.ui.edDataFolder.setText(filename)

    def get_data_folder(self):
        return self.ui.edDataFolder.text()

    def data_folder_changed(self):
        self.model.set_data_folder(self.get_data_folder())
        self.load_model()
