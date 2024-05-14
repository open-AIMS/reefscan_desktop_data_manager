import logging
import sys
import traceback
from time import process_time

from reefscanner.basic_model.basic_model import BasicModel

from aims.operations.abstract_operation import AbstractOperation
from reefcloud.sub_sample import SubSampler

logger = logging.getLogger("")


class ReefcloudSubSampleOperation(AbstractOperation):

    def __init__(self, image_dirs, sample_dir):
        super().__init__()
        self.finished=False
        self.success=False
        self.image_dirs = image_dirs
        self.sample_dir = sample_dir
        self.message = ""
        self.sub_sampler = SubSampler()
        self.selected_photo_infos = None

    def _run(self):
        logger.info(f"start subsample _run {process_time()}")

        self.finished=False
        self.success = True
        logger.info("start subsample")
        self.selected_photo_infos = []
        for camera_id, image_dir in self.image_dirs.items():
            try:
                photo_infos = self.sub_sampler.sub_sample_dir(image_dir=image_dir, sample_dir=self.sample_dir, progress_queue=self.progress_queue)
                self.selected_photo_infos.append(photo_infos)
                self.success = self.success and (photo_infos is not None)
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

