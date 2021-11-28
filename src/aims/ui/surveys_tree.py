import logging
import os

from PyQt5 import QtWidgets, uic
import sys

from PyQt5.QtCore import pyqtSlot, QItemSelection, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView, QPushButton, QWidget, QComboBox, QApplication
from reefscanner.basic_model.reader_writer import save_survey

from aims.gui_model.SurveyTreeModel import SurveyTreeModel
from aims.gui_model.model import GuiModel

from aims.config import Config
from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.load_data import load_data
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.ui.checked_tree_item import CheckTreeitem


logger = logging.getLogger(__name__)

class SurveysTree(object):
    def __init__(self, meipass):
        super().__init__()
        self.meipass = meipass
        self.config_folder ="c:/aims/reef-scanner"
        self.config_file_name = "config.json"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"
        self.app = QtWidgets.QApplication(sys.argv)
        self.start_ui = f'{meipass}resources/surveys-tree.ui'
        self.ui = uic.loadUi(self.start_ui)
        self.config = Config()
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.tree_model = QStandardItemModel()
        self.local_model = GuiModel()
        self.camera_model = GuiModel()
        self.all_surveys = {}
        self.add_tree_data()
        self.lookups()
        self.survey_id = None

        self.ui.btnMap.clicked.connect(self.toggle_map)
        self.ui.btnInfo.clicked.connect(self.toggle_info)
        self.ui.btn_upload.clicked.connect(self.upload)
        self.ui.widEdit.setVisible(False)
        self.ui.widMap.setVisible(False)
        self.ui.widInfo.setVisible(False)

        self.ui.show()
        self.app.exec()

    def survey(self):
        return self.all_surveys[self.survey_id]

    def upload(self):
        # self.model.add_new_sites(self.hardware_sync_model.new_sites)
        surveys_folder = f"{self.local_model.data_folder}/images"
        os.makedirs(surveys_folder, exist_ok=True)
        for survey in self.camera_model.surveys_data.values():
            survey_id = survey["id"]
            survey["folder"] = f"{surveys_folder}/{survey_id}"
            survey["trip"] = self.local_model.trip["uuid"]
            save_survey(survey)

        operation = SyncFromHardwareOperation(self.camera_model.data_folder, self.local_model.data_folder)
        self.aims_status_dialog.set_operation_connections(operation)
        # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()

    def lookups(self):
        cb_site: QComboBox = self.ui.cb_site
        for key, value in self.local_model.surveysModel.sites_lookup.items():
            cb_site.addItem(value, key)

        self.ui.cb_sea.addItem("")
        self.ui.cb_sea.addItem("Calm")
        self.ui.cb_sea.addItem("Medium")
        self.ui.cb_sea.addItem("Rough")

        self.ui.cb_wind.addItem("")
        self.ui.cb_wind.addItem("<5 kn")
        self.ui.cb_wind.addItem("5-10 kn")
        self.ui.cb_wind.addItem("10-15 kn")
        self.ui.cb_wind.addItem("15-20 kn")
        self.ui.cb_wind.addItem("20-25 kn")
        self.ui.cb_wind.addItem("25-30 kn")
        self.ui.cb_wind.addItem(">30 kn")

        self.ui.cb_cloud.addItem("")
        self.ui.cb_cloud.addItem("1 oktas")
        self.ui.cb_cloud.addItem("2 oktas")
        self.ui.cb_cloud.addItem("3 oktas")
        self.ui.cb_cloud.addItem("4 oktas")
        self.ui.cb_cloud.addItem("5 oktas")
        self.ui.cb_cloud.addItem("6 oktas")
        self.ui.cb_cloud.addItem("7 oktas")
        self.ui.cb_cloud.addItem("8 oktas")

        self.ui.cb_vis.addItem("<5m")
        self.ui.cb_vis.addItem("5-10m")
        self.ui.cb_vis.addItem("10-15m")
        self.ui.cb_vis.addItem("15-20m")
        self.ui.cb_vis.addItem("20-25m")
        self.ui.cb_vis.addItem("25-30m")
        self.ui.cb_vis.addItem(">30m")


    def ui_to_data(self):
        if self.survey_id is not None:
            cb_site: QComboBox = self.ui.cb_site
            self.survey()["site"] = cb_site.currentData()
            self.survey()["operator"] = self.ui.ed_operator.text()
            self.survey()["observer"] = self.ui.ed_observer.text()
            self.survey()["vessel"] = self.ui.ed_vessel.text()
            self.survey()["sea"] = self.ui.cb_sea.currentText()

            save_survey(self.survey())


            # self.ui.cb_wind.setCurrentText(self.cur_survey("wind"))
            # self.ui.cb_cloud.setCurrentText(self.cur_survey("cloud"))
            # self.ui.cb_vis.setCurrentText(self.cur_survey("vis"))

    def data_to_ui(self):
        if self.survey_id is not None:
            self.ui.widEdit.setVisible(True)
            cb_site: QComboBox = self.ui.cb_site
            cb_site.setCurrentIndex(cb_site.findData(self.survey_col("site")))
            self.ui.ed_operator.setText(self.survey_col("operator"))
            self.ui.ed_observer.setText(self.survey_col("observer"))
            self.ui.ed_vessel.setText(self.survey_col("vessel"))
            self.ui.cb_sea.setCurrentText(self.survey_col("sea"))
            self.ui.cb_wind.setCurrentText(self.survey_col("wind"))
            self.ui.cb_cloud.setCurrentText(self.survey_col("cloud"))
            self.ui.cb_vis.setCurrentText(self.survey_col("vis"))

            self.ui.lb_sequence_name.setText(self.survey_col("id"))
            self.ui.lb_number_images.setText(self.survey_col("photos"))
            self.ui.lb_start_time.setText(self.survey_col("start_date"))
            self.ui.lb_end_time.setText(self.survey_col("finish_date"))
            self.ui.lb_start_waypoint.setText(f"{self.survey_col('start_lon')} {self.survey_col('start_lat')}")
            self.ui.lb_end_waypoint.setText(f"{self.survey_col('finish_lon')} {self.survey_col('finish_lat')}")
            self.ui.lb_number_images.setText(self.survey_col("photos"))

        else:
            self.ui.widEdit.setVisible(False)

    def survey_col(self, column):
        if column in self.survey():
            return str(self.survey()[column])
        else:
            return ""

    def toggle_map(self):
        wid_map: QWidget = self.ui.widMap
        wid_map.setVisible(not wid_map.isVisible())

    def toggle_info(self):
        wid_info: QWidget = self.ui.widInfo
        wid_info.setVisible(not wid_info.isVisible())

    def add_tree_data(self):
        self.local_model.set_data_folder(self.config.data_folder)
        load_data(self.local_model, aims_status_dialog=self.aims_status_dialog)

        self.camera_model.set_data_folder(self.config.hardware_data_folder)
        load_data(self.camera_model, aims_status_dialog=self.aims_status_dialog)

        duplicate_ids = self.local_model.surveys_data.keys() & self.camera_model.surveys_data.keys()
        if len(duplicate_ids) > 0:
            raise Exception("Surveys on the camera conflict with local surveys.")
        self.all_surveys = {}
        self.all_surveys.update(self.local_model.surveys_data)
        self.all_surveys.update(self.camera_model.surveys_data)

        self.tree_model.itemChanged.connect(self.on_itemChanged)
        view: QTreeView = self.ui.treeView
        view.setHeaderHidden(True)
        view.setModel(self.tree_model)
        view.selectionModel().selectionChanged.connect(self.selection_changed)

        camera_branch = self.make_branch(self.camera_model, 'Reefscan Camera', checkable=True)
        local_branch = self.make_branch(self.local_model, 'Local Drive', checkable=False)

        self.tree_model.appendRow(camera_branch)
        self.tree_model.appendRow(local_branch)

    def make_branch(self, model, name, checkable):
        survey_tree_model = SurveyTreeModel(model, self.local_model.surveysModel.sites_lookup)
        branch = CheckTreeitem(name, checkable)
        sites = survey_tree_model.sites
        for site in sites.keys():
            site_branch = CheckTreeitem(site, checkable)
            branch.appendRow(site_branch)
            surveys = sites[site]
            for survey_id in surveys:
                survey_branch = CheckTreeitem(survey_id, checkable)
                survey_branch.setData(survey_id, Qt.UserRole)
                site_branch.appendRow(survey_branch)
        return branch

    def selection_changed(self,  item_selection:QItemSelection):
        print ("Selection change")
        self.ui_to_data()
        print (item_selection)
        for index in item_selection.indexes():
            self.survey_id = index.data(Qt.UserRole)
            print(self.survey_id)

        self.data_to_ui()



    # @pyqtSlot(QStandardItem)
    def on_itemChanged(self,  item):
        print ("Item change")
        item.cascade_check()
        # state = ['UNCHECKED', 'TRISTATE',  'CHECKED'][item.checkState()]
        # print ("Item with text '%s', is at state %s\n" % ( item.text(),  state))

