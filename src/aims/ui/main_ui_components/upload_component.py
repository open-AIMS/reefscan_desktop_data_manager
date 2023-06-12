import datetime
import os
from time import process_time

from PyQt5 import QtWidgets, QtTest
from PyQt5.QtWidgets import QMessageBox, QApplication, QMainWindow
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.survey import Survey
from reefscanner.basic_model.survey_reefcloud_info import ReefcloudUploadInfo

from aims import state
from aims.gui_model.tree_model import TreeModelMaker, checked_survey_ids, checked_surveys
from aims.operations.load_data import reefcloud_subsample, reefcloud_upload
from reefcloud.reefcloud_utils import upload_file, write_reefcloud_photos_json, update_reefcloud_projects, update_reefcloud_sites
from reefcloud.logon import ReefCloudSession


class UploadComponent():
    def __init__(self, hint_function):
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

    def check_reefcloud_metadata(self, surveys: list[Survey]):
        for survey in surveys:
            best_name = survey.best_name()

            if survey.reefcloud_project is None:
                raise Exception(f"Missing reefcloud project for {best_name}")

            project_ = survey.reefcloud_project
            if not state.config.valid_reefcloud_project(project_):
                raise Exception(f"Invalid reefcloud project {project_} for {best_name}")

            if survey.reefcloud_site is None:
                raise Exception(f"Missing reefcloud site for {best_name}")

            site_ = survey.reefcloud_site
            if not state.config.valid_reefcloud_site(site_, project_):
                raise Exception(f"Invalid reefcloud site {site_} for {best_name}")

    def upload(self):
        print("uploading")
        start = process_time()

        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)

        surveys = checked_surveys(self.surveys_tree_model)

        self.check_reefcloud_metadata(surveys)
        for survey in surveys:
            survey_id = survey.id
            survey_folder = survey.folder
            if survey.reefcloud is not None and survey.reefcloud.total_photo_count == survey.photos:
                # photos are already uploaded just upload the metadata
                upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder,
                            file_name="survey.json")

            else:
                subsampled_image_folder = survey.folder.replace("/reefscan/", "/reefscan_reefcloud/")

                success, selected_photo_infos = reefcloud_subsample(survey_folder, subsampled_image_folder, self.aims_status_dialog)
                if not success:
                    self.aims_status_dialog.close()
                    raise Exception("Cancelled")

                print(selected_photo_infos)
                write_reefcloud_photos_json(survey_id=survey_id,
                                            outputfile=f"{subsampled_image_folder}/photos.json",
                                            selected_photo_infos=selected_photo_infos
                                            )

                success, message = reefcloud_upload(survey, survey_id, survey_folder, subsampled_image_folder, self.aims_status_dialog)
                if not success:
                    self.aims_status_dialog.close()
                    if message is not None:
                        raise Exception(message)
                    else:
                        raise Exception("Cancelled")

        end = process_time()
        minutes = (end-start)/60

        print(f"Upload Finished in {minutes} minutes")
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText("Upload finished")
        errorbox.setDetailedText(f"Finished in {minutes} minutes")

        self.aims_status_dialog.close()

        QtTest.QTest.qWait(200)
        errorbox.exec_()

    def logged_in(self):
        return state.reefcloud_session is not None and state.reefcloud_session.is_logged_in

    def set_hint(self):
        if self.logged_in():
            user_info = state.reefcloud_session.current_user
            self.login_widget.username_label.setText(f"Hello user {user_info.name}.  " + user_info.message)

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
                self.hint_function("Press 'Download Projects and Sites' or check the surveys that you want to upload to reefcloud")
            else:
                self.hint_function("Press the 'Upload Selected Surveys'")

        else:
            self.hint_function("Press the login button")

    def login(self):

        if not self.logged_in():

            print("*******************************************About to attempt login")

            state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)

            result = self.aims_status_dialog.threadPool.apply_async(state.reefcloud_session.login)
            self.login_widget.upload_button.setEnabled(False)
            self.login_widget.login_button.setEnabled(False)
            self.login_widget.update_button.setEnabled(False)
            self.login_widget.cancel_button.setEnabled(True)

            while not result.ready():
                QApplication.processEvents()

            self.login_widget.login_button.setEnabled(True)
            self.login_widget.cancel_button.setEnabled(False)

        self.set_hint()

    def update(self):
        projects_response = update_reefcloud_projects(state.reefcloud_session)
        state.config.load_reefcloud_projects()
        sites_response = update_reefcloud_sites(state.reefcloud_session)
        state.config.load_reefcloud_sites()

        msg_box = QtWidgets.QMessageBox()
        msg_box.setText("Download finished")
        msg_box.setDetailedText(f"{projects_response}\n{sites_response}")
        msg_box.exec_()

    def load_tree(self):
        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)
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


