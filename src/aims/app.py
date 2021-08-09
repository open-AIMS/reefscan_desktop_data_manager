import os
import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QDialog

from aims.trip import TripDlg
from aims.widgets.combo_box_delegate import ComboBoxDelegate
from aims.sites import Sites
from aims.sync.sync_to_reefscan import sync_to_reefscan

from aims.model import Model


# class App(QtWidgets.QMainWindow):
class App(object):

    def __init__(self, meipass, parent=None):
        # super().__init__(parent)
        self.sitesUi = f'{meipass}aims/sites.ui'
        self.tripUi = f'{meipass}aims/trip.ui'
        self.model = Model()
        self.model.setDataFolder("c:/aims/reef-scanner")
        self.app = QtWidgets.QApplication(sys.argv)
        # self.ui=uic.loadUi(ui, baseinstance=self)
        self.ui=uic.loadUi(f'{meipass}aims/app.ui')
        self.ui.setAttribute(Qt.WA_DeleteOnClose)
        self.loadModel()
        self.ui.btnOpenFolder.clicked.connect(self.openDataFolder)
        self.ui.edDataFolder.textChanged.connect(self.dataFolderChanged)
        self.ui.actionSites.triggered.connect(self.editSites)
        self.ui.actionTrip.triggered.connect(self.editTrip)
        self.ui.actionShow_Archives.triggered.connect(self.showArchives)

        self.ui.actionTo_Reefscan.triggered.connect(self.sync_to_reefscan)
        self.ui.tblSurveys.setModel(self.model.surveysModel)
        self.ui.tblSurveys.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.AnyKeyPressed | QAbstractItemView.DoubleClicked)
        self.ui.tblSurveys.clicked.connect(self.tableClicked)
        self.projectsComboBox = ComboBoxDelegate(self.model.surveysModel.projects_lookup)
        self.ui.tblSurveys.setItemDelegateForColumn(1, self.projectsComboBox)
        self.sitesComboBox = ComboBoxDelegate(self.model.surveysModel.sites_lookup)
        self.ui.tblSurveys.setItemDelegateForColumn(2, self.sitesComboBox)

        self.ui.show()
        self.app.exec()

    def sync_to_reefscan(self):
        (message, detailed_message) = sync_to_reefscan(self.model.datafolder)
        print("finished copying")
        messageBox = QtWidgets.QMessageBox()
        messageBox.setText(message)
        messageBox.setDetailedText(detailed_message)
        messageBox.exec_()
        self.loadModel()

    def showArchives(self):
        path=f"{self.model.datafolder}/archive"
        os.startfile(path)

    def tableClicked(self, index):
        if index.column() == 8:
            try:
                path=self.model.surveysModel.data[index.row()]["folder"]
                print(path)
                os.startfile(path)
            except Exception as e:
                print(e)

    def editSites(self):
        try:
            sites=Sites(self.sitesUi, self.model)
            sites.setAttribute(Qt.WA_DeleteOnClose)
            result = sites.exec()
            self.model.makeSitesLookup()
            self.sitesComboBox.setChoices(self.model.sitesLookup)
        except Exception as e:
            print (e)

    def editTrip(self):
        try:
            tripDlg=TripDlg(self.tripUi, self.model.trip)
            tripDlg.setAttribute(Qt.WA_DeleteOnClose)
            tripDlg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
            result = tripDlg.exec()
            print(result)
            if result == QDialog.Accepted:
                print(self.model.trip)
                self.model.makeTripsLookup()
                self.setTrip(self.model.getTripDesc())
                self.model.saveTrip()

        except Exception as e:
            print (e)


    def loadModel(self):
        print("loading model")
        self.setDatafolder(self.model.datafolder)
        self.setTrip(self.model.getTripDesc())

    def setTrip(self, trip):
        self.ui.lblTrip.setText(f'Trip: {trip}')

    def openDataFolder(self):
        filedialog = QtWidgets.QFileDialog(self)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(self.model.datafolder)
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            print(filename)
            self.setDatafolder(filename)

    def setDatafolder(self, filename):
        self.ui.edDataFolder.setText(filename)

    def getDataFolder(self):
        return self.ui.edDataFolder.text()

    def dataFolderChanged(self):
        self.model.setDataFolder(self.getDataFolder())
        self.loadModel()


