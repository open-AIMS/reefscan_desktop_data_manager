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



