import datetime
import os

from reefscanner.basic_model.reader_writer import save_survey

from aims import state
from reefcloud.sub_sample import sub_sample_dir
from reefcloud.reefcloud_utils import upload_file, write_reefcloud_photos_json, user_info
from reefcloud.logon import bens_login


class UploadComponent:
    def __init__(self):
        self.login_widget = None
        self.aims_status_dialog = None

    def load_login_screen(self, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.login_widget.upload_button.clicked.connect(self.upload)
        self.login_widget.login_button.clicked.connect(self.login)

    def upload(self):
        print("uploading")
        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)

        surveys = state.model.surveys_data
        for key in surveys.keys():
            print(key)
            survey = surveys[key]
            print(survey)
            survey_folder = survey["image_folder"]
            survey_name = survey["sequence_name"]
            selected_photo_infos = sub_sample_dir(survey_folder)
            print (selected_photo_infos)
            subsampled_image_folder = survey_folder + "/reefcloud"
            write_reefcloud_photos_json(survey_name=survey_name,
                                        outputfile=f"{subsampled_image_folder}/photos.json",
                                        selected_photo_infos=selected_photo_infos
                                        )

            survey["reefcloud"] = {"uploaded_date": datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"),
                                 "uploaded_photo_count": 0}

            # upload subsampled images
            for file in sorted(os.listdir(subsampled_image_folder)):
                upload_file(tokens=state.tokens, survey_name=survey_name, folder=subsampled_image_folder, file_name=file)
                if "first_file_uploaded" not in survey["reefcloud"]:
                    survey["reefcloud"]["first_photo_uploaded"] = file
                survey["reefcloud"]["last_photo_uploaded"] = file
                if file.lower().endswith(".jpg"):
                    survey["reefcloud"]["uploaded_photo_count"] += 1
                save_survey(survey, state.config.data_folder, state.config.backup_data_folder)


            # upload other files (images or not survey.json)
            for file in os.listdir(survey_folder):
                if (not file.lower().endswith(".jpg")) and file!="survey.json":
                    upload_file(tokens=state.tokens, survey_name=survey_name, folder=survey_folder, file_name=file)

            survey["reefcloud"]["total_photo_count"] = survey["photos"]
            save_survey(survey, state.config.data_folder, state.config.backup_data_folder)

            # upload survey.json last
            upload_file(tokens=state.tokens, survey_name=survey_name, folder=survey_folder, file_name="survey.json")

    def login(self):
        print("*******************************************About to attempt login")
        state.tokens = bens_login(state.config.client_id, state.config.cognito_uri)
        # print("Received token " + state.access_token)
        user = user_info(state.tokens)
        self.login_widget.username_label.setText(f"Hello user {user}")
        print(user)





