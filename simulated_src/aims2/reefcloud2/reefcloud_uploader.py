from reefscanner.basic_model.progress_queue import ProgressQueue
from reefscanner.basic_model.survey import Survey

from aims.messages import messages
from aims2.operations2.count_to_three import count_to_three


class ReefcloudUploader:
    def __init__(self):
        self.canceled = False

    def upload_survey(self, survey: Survey, survey_id, survey_folder, subsampled_image_folder, progress_queue: ProgressQueue):

        count_to_three(progress_queue, f"{messages.upload_survey_message()} {survey.best_name()}")
        return True
