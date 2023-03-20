import datetime
import os

from PyQt5.QtWidgets import QMessageBox
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.survey_reefcloud_info import ReefcloudUploadInfo

from aims import state
from reefcloud.sub_sample import sub_sample_dir
from reefcloud.reefcloud_utils import upload_file, write_reefcloud_photos_json, update_reefcloud_projects, update_reefcloud_sites
from reefcloud.logon import ReefCloudSession


class UploadComponent:
    def __init__(self):
        self.login_widget = None
        self.aims_status_dialog = None

    def load_login_screen(self, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.login_widget.upload_button.clicked.connect(self.upload)
        self.login_widget.login_button.clicked.connect(self.login)
        self.login_widget.update_button.clicked.connect(self.update)


    def check_reefcloud_metadata(self, surveys):
        for survey_id, survey in surveys.items():
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
        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)

        surveys = state.model.surveys_data

        self.check_reefcloud_metadata(surveys)

        for survey_id, survey in surveys.items():
            survey_folder = survey.folder
            subsampled_image_folder = survey.folder.replace("/reefscan/", "/reefscan_reefcloud/")

            selected_photo_infos = sub_sample_dir(survey_folder, subsampled_image_folder)
            print (selected_photo_infos)
            write_reefcloud_photos_json(survey_id=survey_id,
                                        outputfile=f"{subsampled_image_folder}/photos.json",
                                        selected_photo_infos=selected_photo_infos
                                        )

            survey.reefcloud = ReefcloudUploadInfo({"uploaded_date": datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"),
                                 "uploaded_photo_count": 0})


            # upload subsampled images
            for file in sorted(os.listdir(subsampled_image_folder)):
                upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=subsampled_image_folder, file_name=file)
                if file.lower().endswith(".jpg"):
                    if survey.reefcloud.first_photo_uploaded is None:
                        survey.reefcloud.first_photo_uploaded = file
                    survey.reefcloud.last_photo_uploaded = file
                    survey.reefcloud.uploaded_photo_count += 1

                save_survey(survey, state.config.data_folder, state.config.backup_data_folder, False)


            # upload other files (not images or survey.json)
            for file in os.listdir(survey_folder):
                if (not file.lower().endswith(".jpg")) and file!="survey.json":
                    upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder, file_name=file)

            survey.reefcloud.total_photo_count = survey.photos
            save_survey(survey, state.config.data_folder, state.config.backup_data_folder, False)

            # upload survey.json last
            upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder, file_name="survey.json")

    def login(self):
        print("*******************************************About to attempt login")

        state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)
        tokens = state.reefcloud_session.login()

        if state.reefcloud_session.is_logged_in:
            user_info = state.reefcloud_session.current_user
            self.login_widget.username_label.setText(f"Hello user {user_info.name}.  " + user_info.message)
            if not user_info.authorized:
                self.login_widget.upload_button.setEnabled(False)
                self.login_widget.update_button.setEnabled(False)
            else:
                self.login_widget.upload_button.setEnabled(True)
                self.login_widget.update_button.setEnabled(True)

    def update(self):
        update_reefcloud_projects(state.reefcloud_session)
        update_reefcloud_sites(state.reefcloud_session)





