import logging

from PyQt5 import uic
from PyQt5.QtCore import Qt

from aims.ui.surveys_table import SurveysTable

logger = logging.getLogger(__name__)


class Surveys(object):

    def __init__(self, meipass, model):
        # super().__init__(parent)
        self.ui = uic.loadUi(f'{meipass}resources/surveys.ui')
        self.ui.setAttribute(Qt.WA_DeleteOnClose)
        self.model = model


        # self.ui.actionShow_Archives.triggered.connect(self.show_archives)
        # self.ui.actionHardware_Archives.triggered.connect(self.hardware_archives)



        self.surveys_table = SurveysTable(self.ui.tableView, self.model.surveysModel,self.model)
        self.ui.showMaximized()


    # def show_archives(self):
    #     path = f"{self.model.data_folder}/archive"
    #     os.startfile(path)
    #
    # def hardware_archives(self):
    #     path = f"{self.model.hardware_data_folder}/archive"
    #     os.startfile(path)

    # def after_sync(self, args):
    #     message, detailed_message = args
    #     logger.info("after_hardware_sync")
    #     self.load_data()
    #     message_box = QtWidgets.QMessageBox()
    #     message_box.setText(message)
    #     message_box.setDetailedText(detailed_message)
    #     message_box.exec_()

    # def edit_sites(self):
    #     try:
    #         sites = Sites(self.sitesUi, self.model)
    #         sites.setAttribute(Qt.WA_DeleteOnClose)
    #         sites.exec()
    #         self.model.make_sites_lookup()
    #         self.sitesComboBox.setChoices(self.model.surveysModel.sites_lookup)
    #     except Exception as e:
    #         print(e)

    # def edit_trip(self):
    #     try:
    #         trip_dlg = TripDlg(self.tripUi, self.model.trip)
    #         trip_dlg.setAttribute(Qt.WA_DeleteOnClose)
    #         trip_dlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
    #         result = trip_dlg.exec()
    #         if result == QDialog.Accepted:
    #             self.model.make_trips_lookup()
    #             self.set_trip(self.model.get_trip_desc())
    #             self.model.save_trip()
    #
    #     except Exception as e:
    #         print(e)

