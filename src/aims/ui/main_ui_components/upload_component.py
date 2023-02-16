import os

from aims import state
from reefcloud.sub_sample import sub_sample_dir
from reefcloud.upload import upload_file


class UploadComponent:
    def __init__(self):
        self.login_widget = None
        self.aims_status_dialog = None

    def load_login_screen(self, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.login_widget.upload_button.clicked.connect(self.upload)

    def upload(self):
        print("uploading")
        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)

        surveys = state.model.surveys_data
        for key in surveys.keys():
            print(key)
            print(surveys[key])
            survey_folder = surveys[key]["image_folder"]
            survey_name = surveys[key]["sequence_name"]
            sub_sample_dir(survey_folder)
            # upload subsampled images
            subsampled_image_folder = survey_folder + "/reefcloud"
            for file in os.listdir(subsampled_image_folder):
                upload_file (survey_name=survey_name, folder=subsampled_image_folder, file_name=file)

            # upload other files (images or not survey.json)
            for file in os.listdir(survey_folder):
                if (not file.lower().endswith(".jpg")) and file!="survey.json":
                    upload_file(survey_name=survey_name, folder=survey_folder, file_name=file)

            # upload survey.json last
            upload_file(survey_name=survey_name, folder=survey_folder, file_name="survey.json")








