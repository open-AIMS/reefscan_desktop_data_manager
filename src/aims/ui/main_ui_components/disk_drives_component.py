import logging
import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QObject
from PyQt5.QtWidgets import QMessageBox, QMainWindow

from aims.operations.disk_drive_sync import compare
from aims.state import state
logger = logging.getLogger("")

def get_primary_folder(disk):
    return f"{disk}/reefscan".replace("\\", "/")


def has_primary_folder(disk):
    return os.path.exists(get_primary_folder(disk))


def get_secondary_folder(disk):
    return f"{disk}/reefscan_backup".replace("\\", "/")


def has_secondary_folder(disk):
    return os.path.exists(get_secondary_folder(disk))


class DiskDrivesComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.widget = None
        self.aims_status_dialog = None
        self.hint_function = hint_function

    def load_screen(self, fixed_drives, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.widget.driveComboBox.addItem("", None)
        self.widget.secondDriveComboBox.addItem("", None)
        for drive in fixed_drives:
            letter_ = drive['letter']
            label_ = f"{drive['label']}({letter_})"
            self.widget.driveComboBox.addItem(label_, letter_)
            self.widget.secondDriveComboBox.addItem(label_, letter_)
            if has_primary_folder(letter_):
                self.widget.driveComboBox.setCurrentText(label_)
            if has_secondary_folder(letter_):
                self.widget.secondDriveComboBox.setCurrentText(label_)

        self.widget.cbBackup.setChecked(state.config.backup)
        self.widget.secondDriveComboBox.setEnabled(self.widget.cbBackup.isChecked())
        self.widget.cbBackup.stateChanged.connect(self.change_backup)
        self.widget.error_label1.setVisible(False)
        self.widget.error_label2.setVisible(False)
        self.widget.copyButton.setVisible(False)
        self.widget.copyButton.clicked.connect(self.copy)
        self.widget.driveComboBox.currentIndexChanged.connect(self.set_hint)
        self.widget.secondDriveComboBox.currentIndexChanged.connect(self.set_hint)
        self.set_hint()


    def set_hint(self):
        if self.widget.driveComboBox.currentData() is None:
            self.hint_function(self.tr("Choose the primary disk drive to store your data"))
            return
        if self.widget.secondDriveComboBox.currentData() is None:
            self.hint_function(self.tr("Choose the secondary disk drive to store a backup of your data"))
            return

        self.hint_function(self.tr("Press the connect button"))


    def change_backup(self):
        logger.info("changeit")
        self.widget.secondDriveComboBox.setEnabled(self.widget.cbBackup.isChecked())
        self.set_hint()

    def copy(self):
        if state.is_simulated:
            state.backup_drive = None
            state.backup_folder = None
            state.config.backup = False
            self.widget.cbBackup.setChecked(False)
            state.set_data_folders()
        else:
            primary_folder = get_primary_folder(self.widget.driveComboBox.currentData())
            secondary_folder = get_secondary_folder(self.widget.secondDriveComboBox.currentData())
            compare(primary_folder, secondary_folder, True, self.aims_status_dialog)
            self.widget.messageText.setText("")
            self.widget.error_label1.setVisible(False)
            self.widget.error_label2.setVisible(False)
            self.widget.copyButton.setVisible(False)

    def connect(self):
        state.config.backup = self.widget.cbBackup.isChecked()
        # I am leaving this commented code here because it is useful for viewing
        # historic data. Perhaps we need a proper feature for this.
        # state.primary_drive = "Z:/field_data/Trip7565_TorresSTrait_Solander_NAMMA/20210530_Erub/ReefScan_raw/"
        state.primary_drive = self.widget.driveComboBox.currentData()
        state.primary_folder = get_primary_folder(state.primary_drive)
        if not os.path.exists(state.primary_folder):
            os.makedirs(state.primary_folder)

        if state.config.backup:
            state.backup_drive = self.widget.secondDriveComboBox.currentData()
            if state.backup_drive is None or state.backup_drive == "":
                raise Exception("Please choose a backup drive")

            state.backup_folder = get_secondary_folder(state.backup_drive)
            if not os.path.exists(state.backup_folder):
                os.makedirs(state.backup_folder)
            if not self.compare_disks(state.primary_folder, state.backup_folder):
                return False

        else:
            state.config.backup_drive = None
            state.config.backup_folder = None

        state.set_data_folders()

        return True


    def compare_disks(self, primary_folder, secondary_folder):
        total_differences, fixable_messages, unfixable_messages, message_str = compare(primary_folder, secondary_folder, False, self.aims_status_dialog)
        if total_differences > 0:
            message = self.tr("Contents of the primary and seconday drives do not match.")
            message = message + "\n" + message_str

            if len(unfixable_messages) > 0:
                message = message \
                + "\n\n" \
                + self.tr("The following issues cannot be automatically fixed. Please check the disk drives manually.")
                for m in unfixable_messages:
                    message = message + "\n" + m
                if (len(fixable_messages) > 0):
                    message = message + "\n\n" + \
                         self.tr(
                            "The following issues can be fixed automatically after the other issues are rectified.")
                self.widget.error_label2.setText("This cannot be fixed automatically")
                self.widget.copyButton.setVisible(False)

            else:
                self.widget.copyButton.setVisible(True)
                message = message \
                    + "\n" \
                    + self.tr("Do you want to copy all the missing and modified files from the primary to the secondary drive?") \
                    + "\n"
                self.widget.error_label2.setText("Do you want to copy all of the missing and modified files from the primary to the secondary drive?")


            for m in fixable_messages:
                message = message + "\n" + m

            self.widget.messageText.setText(message)
            self.widget.error_label1.setVisible(True)
            self.widget.error_label2.setVisible(True)

            logger.info(fixable_messages)
        return total_differences == 0


