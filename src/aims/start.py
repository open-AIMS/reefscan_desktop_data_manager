import logging
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap
import sys
import os

from aims.before_trip_wizard import BeforeTripWizard
from aims.config_wizard import ConfigWizard
from aims.end_of_day_wizard import EndOfDayWizard
from aims.end_of_trip_wizard import EndOfTripWizard

logger = logging.getLogger(__name__)

class Start(object):
    def __init__(self, meipass):
        super().__init__()
        self.meipass = meipass
        self.config_folder ="c:/aims/reef-scanner"
        self.config_file_name = "config.json"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.app = QtWidgets.QApplication(sys.argv)
        start_ui = f'{meipass}aims/start.ui'
        background_image = f'{meipass}styles/Coraldiseasea.jpg'

        if os.path.exists(background_image):
            logger.info("image exists")
        else:
            logger.info("image not found")
        self.ui = uic.loadUi(start_ui)
        self.ui.lblBackground.setPixmap(QPixmap(background_image))

        self.ui.btnBeforeTrip.clicked.connect(self.before_trip)
        self.ui.btnSetup.clicked.connect(self.setup)
        self.ui.btnEndOfTrip.clicked.connect(self.end_of_trip)
        self.ui.btnEndOfDay.clicked.connect(self.end_of_day)

        self.ui.show()
        self.app.exec()

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
        end_of_day_wizard = EndOfDayWizard(self.meipass)
        end_of_day_wizard.ui.exec()




