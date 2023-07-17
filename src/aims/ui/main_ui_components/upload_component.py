from time import process_time

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


class UploadComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.login_widget = None
        self.aims_status_dialog = None
        self.time_zone = None
        self.hint_function = hint_function

    def load_login_screen(self, aims_status_dialog, time_zone):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone

        self.login_widget.upload_button.clicked.connect(self.upload)
        self.login_widget.login_button.clicked.connect(self.login)
        self.login_widget.update_button.clicked.connect(self.update)
        self.login_widget.cancel_button.clicked.connect(self.cancel)
        self.login_widget.cancel_button.setEnabled(False)
        self.login_widget.upload_button.setEnabled(False)
        self.login_widget.update_button.setEnabled(False)
        self.login_widget.treeView.setEnabled(False)
        self.load_tree()
        self.set_hint()

    def cancel(self):
        print("cancel")
        if state.reefcloud_session is not None:
            state.reefcloud_session.cancel()


    def upload(self):
        print("uploading")
        start = process_time()

        state.config.camera_connected = False
        data_loader.load_data_model(aims_status_dialog=self.aims_status_dialog)
        surveys = checked_surveys(self.surveys_tree_model)
        check_reefcloud_metadata(surveys)

        upload_surveys(surveys, aims_status_dialog = self.aims_status_dialog)

        end = process_time()
        minutes = (end-start)/60

        print(f"Upload Finished in {minutes} minutes")
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText(self.tr("Upload finished"))
        errorbox.setDetailedText(self.tr("Finished in") + f" {minutes} " + self.tr("minutes"))

        self.aims_status_dialog.close()

        QtTest.QTest.qWait(200)
        errorbox.exec_()


    def logged_in(self):
        return state.reefcloud_session is not None and state.reefcloud_session.is_logged_in

    def set_hint(self):
        if self.logged_in():
            user_info = state.reefcloud_session.current_user
            if user_info.authorized:
                message = self.tr("you are authorised to upload data to reefcloud.")
            else:
                message = self.tr("you are not authorised to upload data to reefcloud.")

            self.login_widget.username_label.setText(self.tr("Hello user") + f" {user_info.name}.  " + message)

            if not user_info.authorized:
                self.login_widget.upload_button.setEnabled(False)
                self.login_widget.update_button.setEnabled(False)
                self.login_widget.treeView.setEnabled(False)
            else:
                self.login_widget.upload_button.setEnabled(True)
                self.login_widget.update_button.setEnabled(True)
                self.login_widget.treeView.setEnabled(True)

            surveys = checked_survey_ids(self.surveys_tree_model)
            if len(surveys) == 0:
                self.hint_function(self.tr("Press 'Download Projects and Sites' or check the surveys that you want to upload to reefcloud"))
            else:
                self.hint_function(self.tr("Press the 'Upload Selected Surveys'"))

        else:
            self.hint_function(self.tr("Press the login button"))

    def login(self):

        if not self.logged_in():

            print("*******************************************About to attempt login")

            state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)

            result = self.aims_status_dialog.threadPool.apply_async(state.reefcloud_session.login)
            self.login_widget.upload_button.setEnabled(False)
            self.login_widget.login_button.setEnabled(False)
            self.login_widget.update_button.setEnabled(False)
            self.login_widget.cancel_button.setEnabled(True)
            print("waiting")
            while not result.ready():
                QApplication.processEvents()

            print("logged in")

            self.login_widget.login_button.setEnabled(True)
            self.login_widget.cancel_button.setEnabled(False)

        self.set_hint()

    def update(self):
        projects_response = update_reefcloud_projects(state.reefcloud_session)
        state.config.load_reefcloud_projects()
        sites_response = update_reefcloud_sites(state.reefcloud_session)
        state.config.load_reefcloud_sites()

        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(self.tr("Download finished"))
        msg_box.setDetailedText(f"{projects_response}\n{sites_response}")
        msg_box.exec_()

    def load_tree(self):
        state.config.camera_connected = False
        data_loader.load_data_model(aims_status_dialog=self.aims_status_dialog)
        tree = self.login_widget.treeView
        self.surveys_tree_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_camera=False, checkable=True)
        tree.setModel(self.surveys_tree_model)
        tree.expandRecursively(self.surveys_tree_model.invisibleRootItem().index(), 3)
        self.surveys_tree_model.itemChanged.connect(self.on_itemChanged)

    def on_itemChanged(self, item):
        print ("Item change")
        item.cascade_check()
        surveys = checked_survey_ids(self.surveys_tree_model)
        self.login_widget.upload_button.setEnabled(len(surveys) > 0)
        self.set_hint()


