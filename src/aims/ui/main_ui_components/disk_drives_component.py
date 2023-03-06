import os


def has_primary_folder(disk):
    return os.path.exists(f"{disk}/.reefscan")


def has_secondary_folder(disk):
    return os.path.exists(f"{disk}/.reefscan_backup")

class DiskDrivesComponent:
    def __init__(self):
        self.widget = None
        self.aims_status_dialog = None

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

        self.widget.connectButton.clicked.connect(self.connect)

    def connect(self):
        primary_folder = f"{self.widget.driveComboBox.currentData()}/.reefscan"
        secondary_folder = f"{self.widget.secondDriveComboBox.currentData()}/.reefscan_backup"
        if not os.path.exists(primary_folder):
            os.makedirs(primary_folder)

        if not os.path.exists(secondary_folder):
            os.makedirs(secondary_folder)
