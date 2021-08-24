from PyQt5.QtCore import QRunnable, QMetaObject, Qt, Q_ARG, QThread
from PyQt5.QtWidgets import QProgressDialog

from reefscanner.basic_model.basic_model import BasicModel


class LoadDataOperation(QRunnable):

    def __init__(self, model:BasicModel, progress: QProgressDialog, execute_after):
        QRunnable.__init__(self)
        self.progress = progress
        self.model = model
        self.execute_after = execute_after

    def __del__(self):
        self.execute_after()

    def run(self):
        print("start")
        self.model.read_from_files(self.set_progress_status)

    def set_progress_status(self, function, i):
        QMetaObject.invokeMethod(self.progress, function,
                                 Qt.QueuedConnection, Q_ARG(int, i))
