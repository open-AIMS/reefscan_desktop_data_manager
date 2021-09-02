from PyQt5 import QtCore
from PyQt5.QtCore import QRunnable, QMetaObject, Qt, Q_ARG, QThread
from PyQt5.QtWidgets import QProgressDialog

from aims.operations.abstract_operation import AbstractOperation
from aims.sync.sync_to_reefscan_server import SyncToReefScanServer


class SyncToServerOperation(AbstractOperation):

    def __init__(self, local_folder, server_folder, pull_only):
        super().__init__()
        self.sync = SyncToReefScanServer(self.progress_queue)
        self.local_folder = local_folder
        self.server_folder = server_folder
        self.pull_only = pull_only

    def _run(self):
        print("start")
        if self.pull_only:
            return self.sync.pull_from_server(self.local_folder, self.server_folder)
        else:
            return self.sync.sync(self.local_folder, self.server_folder)

