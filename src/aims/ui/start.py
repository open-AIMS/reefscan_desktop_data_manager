import logging
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap
import sys
import os

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.ui.before_trip_wizard import BeforeTripWizard
from aims.config import Config
from aims.ui.config_wizard import ConfigWizard
from aims.ui.end_of_day_wizard import EndOfDayWizard
from aims.ui.end_of_trip_wizard import EndOfTripWizard
from aims.gui_model.model import GuiModel
from aims.ui.surveys import Surveys
from aims.ui.sites import Sites
from aims.operations.load_data import load_data
from aims.ui.trip import TripDlg

logger = logging.getLogger(__name__)

class Start(object):
    def __init__(self, meipass):
        super().__init__()
        self.meipass = meipass
        self.config_folder ="c:/aims/reef-scanner"
        self.config_file_name = "config.json"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.app = QtWidgets.QApplication(sys.argv)
        self.start_ui = f'{meipass}resources/start.ui'
        self.ui = uic.loadUi(self.start_ui)

        self.model = GuiModel()
        self.config = Config(self.model)
        self.aims_status_dialog = AimsStatusDialog(self.ui)

        background_image = f'{meipass}resources/Coraldiseasea.jpg'

        if os.path.exists(background_image):
            logger.info("image exists")
        else:
            logger.info("image not found")
        self.ui.lblBackground.setPixmap(QPixmap(background_image))

        self.ui.btnBeforeTrip.clicked.connect(self.before_trip)
        self.ui.btnSetup.clicked.connect(self.setup)
        self.ui.btnEndOfTrip.clicked.connect(self.end_of_trip)
        self.ui.btnEndOfDay.clicked.connect(self.end_of_day)
        self.ui.btnViewSurveys.clicked.connect(self.surveys)
        self.ui.btnViewSites.clicked.connect(self.sites)
        self.ui.btnTrip.clicked.connect(self.trip)

        self.ui.actionLocal.triggered.connect(self.show_archives)
        self.ui.actionHardware.triggered.connect(self.hardware_archives)

        self.surveys_dlg = None
        self.sites_dlg = None

        self.ui.show()
        self.app.exec()

    def show_archives(self):
        path = f"{self.model.data_folder}/archive"
        os.startfile(path)

    def hardware_archives(self):
        path = f"{self.model.hardware_data_folder}/archive"
        os.startfile(path)


    def before_trip(self):
        print("before trip")
        before_trip_wizard = BeforeTripWizard(self.meipass)
        before_trip_wizard.ui.exec()

    def end_of_trip(self):
        print("end of trip")
        end_of_trip_wizard = EndOfTripWizard(self.meipass)
        end_of_trip_wizard.ui.exec()

    def setup(self):
        config_wizard = ConfigWizard(self.meipass)
        config_wizard.ui.exec()

    def end_of_day(self):
        self.load_data()
        end_of_day_wizard = EndOfDayWizard(self.meipass, self.model)
        end_of_day_wizard.ui.exec()

    def surveys(self):
        self.load_data()
        self.surveys_dlg = Surveys(self.meipass, self.model)

    def sites(self):
        self.load_data()
        self.sites_dlg = Sites(self.meipass, self.model)

    def trip(self):
        self.load_data()
        self.trip_dlg = TripDlg(self.meipass, self.model)

    def load_data(self):
        load_data(self.model, self.aims_status_dialog)


