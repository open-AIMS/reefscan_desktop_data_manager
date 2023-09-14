import os
from datetime import datetime

from PyQt5.QtCore import QObject
from reefscanner.basic_model.progress_queue import ProgressQueue
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.survey import Survey
from reefscanner.basic_model.survey_reefcloud_info import ReefcloudUploadInfo

from aims.messages import messages
from aims.state import state
from aims2.reefcloud2.reefcloud_utils import upload_file
import logging
logger = logging.getLogger("")

class ReefcloudUploader(QObject):
    def __init__(self):
        super().__init__()
        self.canceled = False

    def upload_survey(self, survey: Survey, survey_id, survey_folder, subsampled_image_folder, progress_queue: ProgressQueue):

        progress_queue.reset()
        progress_queue.set_progress_label(f"{messages.upload_survey_message()} {survey.best_name()}")

        survey.reefcloud = ReefcloudUploadInfo({"uploaded_date": datetime.now().strftime("%Y-%m-%dT%H%M%S"),
                                                "uploaded_photo_count": 0})
        # upload subsampled images
        files = os.listdir(subsampled_image_folder)
        progress_queue.set_progress_max(len(files))
        for file in sorted(files):
            if self.canceled:
                return False
            upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=subsampled_image_folder,
                        file_name=file)
            if file.lower().endswith(".jpg"):
                if survey.reefcloud.first_photo_uploaded is None:
                    survey.reefcloud.first_photo_uploaded = file
                survey.reefcloud.last_photo_uploaded = file
                survey.reefcloud.uploaded_photo_count += 1
                save_survey(survey, state.primary_folder, state.backup_folder, False)

            progress_queue.set_progress_value()
        # upload other files (not images or survey.json)
        for file in os.listdir(survey_folder):
            if (not file.lower().endswith(".jpg")) and file != "survey.json":
                upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder,
                            file_name=file)
        survey.reefcloud.total_photo_count = survey.photos
        save_survey(survey, state.primary_folder, state.backup_folder, False)
        # upload survey.json last
        upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder,
                    file_name="survey.json")

        return True