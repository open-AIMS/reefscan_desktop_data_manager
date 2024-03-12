import logging
from time import process_time
from typing import List

from PyQt5 import QtWidgets, QtTest
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication
from reefscanner.basic_model.survey import Survey

from aims import data_loader
from aims.state import state
from aims.gui_model.tree_model import TreeModelMaker, checked_survey_ids, checked_surveys
from aims2.reefcloud2.reefcloud_utils import upload_file, write_reefcloud_photos_json, update_reefcloud_projects, \
    update_reefcloud_sites, check_reefcloud_metadata
from aims2.reefcloud2.reefcloud_session import ReefCloudSession
from aims2.reefcloud2.upload_surveys import upload_surveys

logger = logging.getLogger("")
class UploadComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.upload_widget = None
        self.aims_status_dialog = None
        self.time_zone = None
        self.hint_function = hint_function

    def load(self, aims_status_dialog, time_zone):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone
        self.upload_widget.upload_button.clicked.connect(self.upload)
        self.upload_widget.max_distance_edit.setInputMask("00")
        self.upload_widget.max_distance_edit.setText(state.reef_cloud_max_depth)
        self.upload_widget.max_distance_edit.editingFinished.connect(self.save_max_distance_to_config)

        self.load_tree()
        self.set_hint()

    def save_max_distance_to_config(self):
        state.reef_cloud_max_depth = self.upload_widget.max_distance_edit.text()
        state.save_config_file()

    def upload(self):
        logger.info("uploading")

        start = process_time()

        state.config.camera_connected = False
        data_loader.load_data_model(aims_status_dialog=self.aims_status_dialog)
        surveys = checked_surveys(self.surveys_tree_model)
        check_reefcloud_metadata(surveys)

        if state.config.clear_reefcloud:
            self.clear_reefcloud(surveys)

        upload_surveys(surveys, aims_status_dialog = self.aims_status_dialog)

        end = process_time()
        minutes = (end-start)/60

        logger.info(f"Upload Finished in {minutes} minutes")
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText(self.tr("Upload finished. Your data should be available in ReefCloud within half an hour."))
        errorbox.setDetailedText(self.tr("Finished in") + f" {minutes} " + self.tr("minutes"))

        self.aims_status_dialog.close()

        QtTest.QTest.qWait(200)
        errorbox.exec_()

    def clear_reefcloud(self, surveys: List[Survey]):
        for survey in surveys:
            survey.reefcloud = None

    def set_hint(self):
        surveys = checked_survey_ids(self.surveys_tree_model)
        if len(surveys) == 0:
            self.hint_function(self.tr("Check the surveys that you want to upload to reefcloud"))
        else:
            self.hint_function(self.tr("Press the 'Upload Selected Surveys'"))

    def load_tree(self):
        state.config.camera_connected = False
        data_loader.load_data_model(aims_status_dialog=self.aims_status_dialog)
        tree = self.upload_widget.treeView
        self.surveys_tree_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_camera=False, checkable=True)
        tree.setModel(self.surveys_tree_model)
        tree.expandRecursively(self.surveys_tree_model.invisibleRootItem().index(), 3)
        self.surveys_tree_model.itemChanged.connect(self.on_itemChanged)

    def on_itemChanged(self, item):
        print ("Item change")
        item.cascade_check()
        surveys = checked_survey_ids(self.surveys_tree_model)
        self.upload_widget.upload_button.setEnabled(len(surveys) > 0)
        self.set_hint()


