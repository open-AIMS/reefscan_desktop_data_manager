from PyQt5.QtWidgets import QAbstractItemView, QDialog, QProgressDialog
from PyQt5.QtCore import Qt
import logging
from threading import RLock
from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)


class AimsStatusDialog(object):
    def __init__(self, ui):
        super().__init__()

        self.ui = ui

        self.progress_dialog = QProgressDialog("Syncing data.", "Cancel", 0, 1, self.ui)
        self.progress_dialog.setValue(1)
        self.progress_dialog.setMinimumDuration(10)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.redrawLock = RLock()
        self.threadPool = ThreadPool(16)

    def set_progress_value(self, params):
        (i, label) = params
        try:
            logger.info(f"value {i}")
            with self.redrawLock:
                self.progress_dialog.setValue(i)
                self.progress_dialog.setLabelText(label)
        except Exception as e:
            print("ERROR")
            logger.error("ERROR")
            print(str(e))

    def set_progress_max(self, i):
        logger.info(f"max {i}")
        with self.redrawLock:
            self.progress_dialog.setMaximum(i)

    def set_operation_connections(self, operation):
        self.progress_dialog.canceled.connect(operation.cancel)
        operation.set_max.connect(self.set_progress_max)
        operation.set_value.connect(self.set_progress_value)
        operation.exception.connect(self.throw_exception)

    def throw_exception(self, e):
        logger.info("throw exception")
        raise e
