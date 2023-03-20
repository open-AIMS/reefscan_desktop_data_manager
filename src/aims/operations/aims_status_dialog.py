from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt
import logging
from threading import RLock, Timer
from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)


class AimsStatusDialog(object):
    def __init__(self, ui):
        super().__init__()

        self.ui = ui

        self.progress_dialog = None
        self.redrawLock = RLock()
        self.threadPool = ThreadPool(16)
        self.operation = None

    def make_progress_dialog(self):
        self.progress_dialog = QProgressDialog("Syncing data.", "Cancel", 0, 1, self.ui)
        self.progress_dialog.setWindowTitle("Wait...")
        self.progress_dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.progress_dialog.setValue(1)
        self.progress_dialog.setMinimumDuration(10)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        # self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAttribute(Qt.WA_DeleteOnClose, True);

    def set_progress_value(self, params):
        (i, label) = params
        try:
            logger.debug(f"value {i}")
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
        self.make_progress_dialog()
        self.progress_dialog.canceled.connect(operation.cancel)
        self.operation = operation
        operation.set_max.connect(self.set_progress_max)
        operation.set_value.connect(self.set_progress_value)
        operation.exception.connect(self.throw_exception)

    def close(self):
        self.progress_dialog.close()
        # timer = Timer(0.5, self.progress_dialog.close)
        # timer.start()

    def throw_exception(self, e):
        logger.info("throw exception")
        raise e

