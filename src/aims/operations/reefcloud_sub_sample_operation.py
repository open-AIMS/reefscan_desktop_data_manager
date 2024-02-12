import logging
import sys
import traceback
from time import process_time

from reefscanner.basic_model.basic_model import BasicModel

from aims.operations.abstract_operation import AbstractOperation
from reefcloud.sub_sample import SubSampler

logger = logging.getLogger("")


class ReefcloudSubSampleOperation(AbstractOperation):

    def __init__(self, image_dir, sample_dir):
        super().__init__()
        self.finished=False
        self.success=False
        self.image_dir = image_dir
        self.sample_dir = sample_dir
        self.message = ""
        self.sub_sampler = SubSampler()
        self.selected_photo_infos = None

    def _run(self):
        logger.info(f"start subsample _run {process_time()}")

        self.finished=False
        self.success = False
        logger.info("start subsample")
        try:
            self.selected_photo_infos = self.sub_sampler.sub_sample_dir(image_dir=self.image_dir, sample_dir=self.sample_dir, progress_queue=self.progress_queue)
            self.success = self.selected_photo_infos is not None
        except Exception as e:
            logger.error("ERROR ERROR")
            traceback.print_exc()
            self.message = str(e)

            self.success = False

        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            self.sub_sampler.canceled = True

