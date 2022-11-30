from fabric import Connection
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims import state
from aims.operations.archive_checker import ArchiveChecker


class ArchiveComponent:

    def __init__(self, archive_widget):
        self.archive_widget = archive_widget
        self.archive_widget.btnCheck.clicked.connect(self.check)
        self.archive_widget.btnDelete.clicked.connect(self.delete)
        self.samba_file_ops = get_file_ops(True)
        self.archive_checker = ArchiveChecker()
        self.archive_checker.progress.connect(self.set_progress_value)

        self.files_deleted = 0

    def cancel_checker(self):
        self.archive_checker.cancel()

    def set_progress_value(self, val):
        self.archive_widget.textEdit.setText(val)

    def check(self):
        print ("Checking")
        self.archive_widget.textEdit.setText("Checking...")
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

