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


class ReefcloudConnectComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.login_widget = None
        self.aims_status_dialog = None
        self.time_zone = None
        self.hint_function = hint_function

    def load(self, aims_status_dialog, time_zone):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone

        self.login_widget.cancel_button.clicked.connect(self.cancel)
        self.login_widget.cancel_button.setEnabled(False)
        self.set_hint()

    def cancel(self):
        print("cancel")
        if state.reefcloud_session is not None:
            state.reefcloud_session.cancel()


    def logged_in(self):
        return state.reefcloud_session is not None and state.reefcloud_session.is_logged_in

    def set_hint(self):
        if self.logged_in():
            user_info = state.reefcloud_session.current_user
            if user_info.authorized:
                message = self.tr("you are authorised to upload data to reefcloud.")
            else:
                message = self.tr("you are not authorised to upload data to reefcloud.")

            self.login_widget.username_label.setText(self.tr("Hello ") + f" {user_info.name}.  " + message)

        else:
            self.hint_function(self.tr("Press the login button"))


    def update(self):
        projects_response = update_reefcloud_projects(state.reefcloud_session)
        state.config.load_reefcloud_projects()
        sites_response = update_reefcloud_sites(state.reefcloud_session)
        state.config.load_reefcloud_sites()

        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(self.tr("Download finished"))
        msg_box.setDetailedText(f"{projects_response}\n{sites_response}")
        msg_box.exec_()

    def login(self):

        if not self.logged_in():

            print("*******************************************About to attempt login")

            state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)

            result = self.aims_status_dialog.threadPool.apply_async(state.reefcloud_session.login)
            self.login_widget.login_button.setEnabled(False)
            self.login_widget.cancel_button.setEnabled(True)
            print("waiting")
            while not result.ready():
                QApplication.processEvents()

            print("logged in")

            self.login_widget.login_button.setEnabled(True)
            self.login_widget.cancel_button.setEnabled(False)

        if self.logged_in():
            self.update()

        self.set_hint()
        return self.logged_in()
