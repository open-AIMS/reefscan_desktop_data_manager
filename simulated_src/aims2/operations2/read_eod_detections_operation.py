import logging
import traceback

from aims.model.cots_detection_list import CotsDetectionList
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger("")


class ReadEodDetectionsOperation(AbstractOperation):
    def __init__(self, folder, cots_detection_list: CotsDetectionList, samba=False, use_cache=True):
        super().__init__()
        self.success=False
        self.message = ""
        self.finished=False


    def _run(self):
        self.success=True
        self.message = ""
        self.finished=True



