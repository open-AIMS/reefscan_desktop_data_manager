import logging
import sys
import traceback

from reefscanner.basic_model.basic_model import BasicModel
from reefscanner.basic_model.progress_queue import ProgressQueue
from reefscanner.basic_model.survey import Survey

from aims.operations.abstract_operation import AbstractOperation
from reefcloud.reefcloud_uploader import ReefcloudUploader
from reefcloud.sub_sample import SubSampler

logger = logging.getLogger("")


class ReefcloudUploadOperation(AbstractOperation):

    def __init__(self, survey: Survey, survey_id, survey_folder, subsampled_image_folder):
        super().__init__()
        self.finished=False
        self.success=False
        self.message = None
        self.uploader = ReefcloudUploader()
        self.selected_photo_infos = None
        self.survey = survey
        self.survey_id = survey_id
        self.survey_folder = survey_folder
        self.subsampled_image_folder = subsampled_image_folder


    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start subsample")
        try:
            self.success = self.uploader.upload_survey(self.survey, self.survey_id, self.survey_folder, self.subsampled_image_folder, self.progress_queue)
        except Exception as e:
            logger.error("ERROR ERROR")
            traceback.print_exc()
            self.message = str(e)
            print(self.message)
            self.success = False

        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            self.uploader.canceled = True

