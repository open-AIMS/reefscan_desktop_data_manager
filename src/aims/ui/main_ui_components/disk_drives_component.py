import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox

from aims import state
from aims.operations.disk_drive_sync import compare


def get_primary_folder(disk):
    return f"{disk}/reefscan"


def has_primary_folder(disk):
    return os.path.exists(get_primary_folder(disk))


def get_secondary_folder(disk):
    return f"{disk}/reefscan_backup"


def has_secondary_folder(disk):
    return os.path.exists(get_secondary_folder(disk))


class DiskDrivesComponent:
    def __init__(self, parent):
        self.widget = None
        self.aims_status_dialog = None
        self.parent = None

    def load_screen(self, fixed_drives, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
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

    def change_backup(self):
        print("changeit")
        self.widget.secondDriveComboBox.setEnabled(self.widget.cbBackup.isChecked())

    def connect(self):
        state.config.backup = self.widget.cbBackup.isChecked()
        primary_folder = get_primary_folder(self.widget.driveComboBox.currentData())
        if not os.path.exists(primary_folder):
            os.makedirs(primary_folder)

        state.config.data_folder = primary_folder

        if state.config.backup:
            secondary_folder = get_secondary_folder(self.widget.secondDriveComboBox.currentData())
            if not os.path.exists(secondary_folder):
                os.makedirs(secondary_folder)
            state.config.backup_data_folder = secondary_folder
            self.compare_disks(primary_folder, secondary_folder)
        else:
            state.config.backup_data_folder = None

        state.set_data_folders()
        state.config.save_config_file()

        return False


    def compare_disks(self, primary_folder, secondary_folder):
        total_differences, messages, message_str = compare(primary_folder, secondary_folder, False)
        if total_differences > 0:
            message = f"""
                Contents of the primary and seconday drives do not match.\n
                Do you want to copy all the missing and modified files from the primary to the secondary drive? \n
                {message_str} 
            """

            self.widget.messageText.setText(message_str)
            print(messages)


