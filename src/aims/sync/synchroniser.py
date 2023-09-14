import logging
import shutil
import os
from datetime import datetime

from PyQt5.QtCore import QObject
from joblib import Parallel, delayed
from reefscanner.basic_model.progress_queue import ProgressQueue

logger = logging.getLogger("")


class Synchroniser(QObject):
    def __init__(self, progress_queue: ProgressQueue):
        super().__init__()
        self.files_to_copy: list[tuple[str]] = []
        self.total_files = 0
        # self.cancelled = False
        self.progress_queue = progress_queue

    def cancel(self):
        self.cancelled = True

    def _ignore_copy(self, path, names):
        if self.cancelled:
            return names   # everything ignored
        else:
            return []   # nothing will be ignored

    def prepare_copy(self, src, dst):
        if self.cancelled:
            logger.info("cancelled")
        else:
            cnt = len(self.files_to_copy)
            if cnt % 100 == 0:
                message = f'Counting files. So far {cnt}'
                self.progress_queue.set_progress_label(message)
            # logger.info(message)
            self.files_to_copy.append((src, dst))

