from time import process_time, sleep

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QObject
import logging
from threading import RLock, Timer
from multiprocessing.pool import ThreadPool

logger = logging.getLogger("AimsStatusDialog")


class AimsStatusDialog(QObject):
    def __init__(self, ui):
        super().__init__()

        self.ui = ui

        self.progress_dialog = None
        self.redrawLock = RLock()
        self.threadPool = ThreadPool(16)
        self.operation = None

    def make_progress_dialog(self):
        self.progress_dialog = QProgressDialog(self.tr("Syncing data."), self.tr("Cancel"), 0, 1, self.ui)
        self.progress_dialog.setWindowTitle(self.tr("Wait..."))
        self.progress_dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.progress_dialog.setValue(1)
        self.progress_dialog.setMinimumDuration(10)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        # self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAttribute(Qt.WA_DeleteOnClose, True)

    def set_progress_value(self, params):
        (i, label) = params
        try:
            # logger.info(f"value {i} {label} {process_time()}")
            with self.redrawLock:
                self.progress_dialog.setValue(i)
                self.progress_dialog.setLabelText(label)
        except Exception as e:
            logger.error("ERROR setting value")
            logger.info(str(e))

    def set_progress_max(self, i):
        # logger.info(f"max {i}")
        try:
            with self.redrawLock:
                self.progress_dialog.setMaximum(i)
        except Exception as e:
            logger.error("ERROR setting max")
            logger.info(str(e))

    def set_operation_connections(self, operation):
        self.make_progress_dialog()
        self.progress_dialog.canceled.connect(operation.cancel)
        self.operation = operation
        operation.set_max.connect(self.set_progress_max)
        operation.set_value.connect(self.set_progress_value)
        operation.exception.connect(self.throw_exception)
        sleep(0.1)

    def close(self):
        # Close seems to trigger the cancel signal and sometimes we need to know
        # that the job was cancelled by the user
        try:
            self.progress_dialog.canceled.disconnect(self.operation.cancel)
        except:
            logger.warn("error disconnecting status box")
        try:
            self.progress_dialog.close()
        except:
            logger.warn("error closing status box")
        # timer = Timer(0.5, self.progress_dialog.close)
        # timer.start()

    def throw_exception(self, e):
        logger.info("throw exception")
        raise e

