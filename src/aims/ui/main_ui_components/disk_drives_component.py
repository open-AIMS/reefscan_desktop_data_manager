import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox

from aims import state
from aims.operations.disk_drive_sync import compare


def get_primary_folder(disk):
    return f"{disk}/reefscan".replace("\\", "/")


def has_primary_folder(disk):
    return os.path.exists(get_primary_folder(disk))


def get_secondary_folder(disk):
    return f"{disk}/reefscan_backup".replace("\\", "/")


def has_secondary_folder(disk):
    return os.path.exists(get_secondary_folder(disk))


class DiskDrivesComponent:
    def __init__(self, hint_function):
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
            self.hint_function("Choose the primary disk drive to store your data")
            return
        if self.widget.secondDriveComboBox.currentData() is None:
            self.hint_function("Choose the secondary disk drive to store a backup of your data")
            return

        self.hint_function("Press the connect button")


    def change_backup(self):
        print("changeit")
        self.widget.secondDriveComboBox.setEnabled(self.widget.cbBackup.isChecked())
        self.set_hint()

    def copy(self):
        primary_folder = get_primary_folder(self.widget.driveComboBox.currentData())
        secondary_folder = get_secondary_folder(self.widget.secondDriveComboBox.currentData())
        compare(primary_folder, secondary_folder, True, self.aims_status_dialog)

    def connect(self):
        state.config.backup = self.widget.cbBackup.isChecked()
        state.primary_drive = self.widget.driveComboBox.currentData()
        state.primary_folder = get_primary_folder(state.primary_drive)
        if not os.path.exists(state.primary_folder):
            os.makedirs(state.primary_folder)

        if state.config.backup:
            state.backup_drive = self.widget.secondDriveComboBox.currentData()
            state.backup_folder = get_secondary_folder(state.backup_drive)
            if not os.path.exists(state.backup_folder):
                os.makedirs(state.backup_folder)
            if not self.compare_disks(state.primary_folder, state.backup_folder):
                return False

        else:
            state.config.backup_drive = None
            state.config.backup_folder = None

        state.set_data_folders()
        state.config.save_config_file()

        return True


    def compare_disks(self, primary_folder, secondary_folder):
        total_differences, messages, message_str = compare(primary_folder, secondary_folder, False, self.aims_status_dialog)
        if total_differences > 0:
            message = f"""
                Contents of the primary and seconday drives do not match.\n
                Do you want to copy all the missing and modified files from the primary to the secondary drive? \n
                {message_str} 
            """

            self.widget.messageText.setText(message_str)
            self.widget.error_label1.setVisible(True)
            self.widget.error_label2.setVisible(True)
            self.widget.copyButton.setVisible(True)

            print(messages)
        return total_differences == 0


