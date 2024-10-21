import logging
import traceback

from aims.model.cots_detection_list import CotsDetectionList
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger("")


class ReadEodDetectionsOperation(AbstractOperation):
    def __init__(self, folder, cots_detection_list: CotsDetectionList, samba=False, use_cache=True):
        super().__init__()

        self.folder = folder
        self.cots_detection_list = cots_detection_list
        self.samba = samba
        self.use_cache = use_cache
        self.success=False
        self.message = ""
        self.finished=False

    def _run(self):
        self.success=False
        self.message = ""
        self.finished=False
        try:
            self.cots_detection_list.read_eod_files(self.progress_queue, self, self.folder, samba=self.samba, use_cache=self.use_cache)
            self.success=True
        except Exception as e:
            logger.error("ERROR ERROR: resd_eod_detections_operation from real_src")
            traceback.print_exc()
            self.message = str(e)
            logger.info(self.message)
            logger.error(self.message)
            self.success = False
        self.finished=True



