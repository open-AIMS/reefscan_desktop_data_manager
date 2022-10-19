from PyQt5 import uic, QtCore
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QMainWindow
from fabric import Connection
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims import state
from aims.operations.archive_checker import ArchiveChecker


class ArchiveUi(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = f'{state.meipass}resources/archive.ui'
        self.ui = uic.loadUi(ui_file)
        self.ui.btnCheck.clicked.connect(self.check)
        self.ui.btnDelete.clicked.connect(self.delete)
        self.samba_file_ops = get_file_ops(True)
        self.archive_checker = ArchiveChecker()
        self.archive_checker.progress.connect(self.set_progress_value)
        self.ui.centralwidget.installEventFilter(self)
        self.ui.setWindowFlags(self.ui.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.ui.setWindowFlags(self.ui.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.files_deleted = 0

    def eventFilter(self, source, event):
        if event.type() == QEvent.Hide:
            print("cancel")
            self.archive_checker.cancel()

        return super(ArchiveUi, self).eventFilter(source, event)

    def set_progress_value(self, val):
        self.ui.textEdit.setText(val)

    def show(self):
        self.ui.show()

    def check(self):
        print ("Checking")
        self.ui.textEdit.setText("Checking...")
        self.archive_checker.run()
        # archive_stats = ArchiveStats()
        # get_archive_stats(state.model, archive_stats)
        # self.ui.textEdit.setText(archive_stats.to_string())

    def delete(self):
        self.archive_checker.cancel()
        print("delete")
        archive_folder = state.config.camera_images_folder + "/archive"
        conn = Connection(
            "jetson@" + state.config.camera_ip,
            connect_kwargs={"password": "jetson"}
        )
        conn.run("rm -r " + archive_folder)

        # self.files_deleted = 0
        # if self.samba_file_ops.isdir(archive_folder):
        #     self.delete_recursive_samba(archive_folder)

        self.check()

    def delete_recursive_samba(self, file_or_folder):
        if self.samba_file_ops.isdir(file_or_folder):
            children = self.samba_file_ops.listdir(file_or_folder)
            for child in children:
                file_name = file_or_folder + "/" + child
                self.delete_recursive_samba(file_name)
            self.samba_file_ops.rmdir(file_or_folder)
        else:
            self.samba_file_ops.remove(file_or_folder)
            self.files_deleted += 1
            print(self.files_deleted)






