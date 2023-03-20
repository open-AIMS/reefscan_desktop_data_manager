import datetime
import os
import shutil
import time

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QWidget, QFileSystemModel, QComboBox, QAction, QMenu, QInputDialog, \
    QApplication, QMessageBox, QListView, QListWidget, QLabel, QTableView
from PyQt5 import QtWidgets, uic, QtCore
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims import state
import sys
import logging
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent, QStandardPaths, QDir

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.archive_checker import ArchiveChecker
from aims.ui.main_ui_components.data_component import DataComponent
from aims.ui.main_ui_components.disk_drives_component import DiskDrivesComponent
from aims.ui.main_ui_components.upload_component import UploadComponent
from aims.ui.main_ui_components.utils import clearLayout, setup_file_system_tree_and_combo_box
import win32file
import win32api
from pytz import common_timezones, all_timezones, timezone, utc
from tzlocal import get_localzone
import unicodedata
from aims.ui import deselectable_tree_view

logger = logging.getLogger(__name__)

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")


workflow_button_border = ";border: 5px solid red;"


def add_button_border(button):
    style = button.styleSheet()
    style = style + workflow_button_border
    button.setStyleSheet(style)


def remove_button_border(button):
    style = button.styleSheet()
    style = style.replace(workflow_button_border, "")
    button.setStyleSheet(style)




class MainUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_screen = "start"
        self.app = QtWidgets.QApplication(sys.argv)
        self.start_ui = f'{state.meipass}resources/main.ui'
        self.ui = uic.loadUi(self.start_ui)

        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)

        self.data_component = DataComponent(hint_function=self.hint)
        self.upload_component = UploadComponent()
        self.disk_drives_component = DiskDrivesComponent(hint_function=self.hint)

        self.workflow_widget = None
        self.connect_widget = None
        self.status_widget = None

        self.time_zone = None
        self.fixed_drives = None

        self.setup_workflow()
        self.setup_status()
        self.setup_timezone()

        self.load_start_screen()
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.archive_checker = ArchiveChecker()
        self.update_status()
        self.camera_connected = False
        self.drives_connected = False

        self.hint('Choose "Connect Disks" from the workflow bar')

    def hint(self, text):
        self.ui.hint_label.setText(text)

    def setup_timezone(self):
        localzone = get_localzone()
        self.time_zone = localzone

    def setup_status(self):
        status_widget_file = f'{state.meipass}resources/status-bar.ui'
        self.status_widget: QWidget = uic.loadUi(status_widget_file)
        self.ui.statusFrame.layout().addWidget(self.status_widget)
        self.status_widget.refreshButton.clicked.connect(self.update_status)

    def highlight_button(self, button):
        remove_button_border(self.workflow_widget.connectDisksButton)
        self.workflow_widget.connectDisksButton.setEnabled(True)
        remove_button_border(self.workflow_widget.connectButton)
        self.workflow_widget.connectButton.setEnabled(self.drives_connected)
        remove_button_border(self.workflow_widget.dataButton)
        self.workflow_widget.dataButton.setEnabled(self.drives_connected)
        remove_button_border(self.workflow_widget.uploadButton)
        self.workflow_widget.uploadButton.setEnabled(self.drives_connected)

        add_button_border(button)
        button.setEnabled(False)

    def setup_workflow(self):
        workflow_widget_file = f'{state.meipass}resources/workflow-bar.ui'
        self.workflow_widget: QWidget = uic.loadUi(workflow_widget_file)
        self.ui.workflowFrame.layout().addWidget(self.workflow_widget)
        self.workflow_widget.connectButton.clicked.connect(self.load_connect_screen)
        self.workflow_widget.connectButton.setEnabled(False)
        self.workflow_widget.dataButton.setEnabled(False)
        self.workflow_widget.uploadButton.setEnabled(False)
        self.workflow_widget.uploadButton.clicked.connect(self.load_upload_screen)
        self.workflow_widget.dataButton.clicked.connect(self.load_data_screen)
        self.workflow_widget.connectDisksButton.clicked.connect(self.load_connect_disks_screen)

    def ui_to_data(self):
        if self.current_screen == "data":
            self.data_component.ui_to_data()

    def load_upload_screen(self):
        self.ui_to_data()
        self.current_screen = "upload"

        self.upload_component.login_widget = self.load_main_frame(f'{state.meipass}resources/cloud-log-in.ui')
        self.upload_component.load_login_screen(aims_status_dialog=self.aims_status_dialog)
        self.highlight_button(self.workflow_widget.uploadButton)

    def load_start_screen(self):
        self.load_main_frame(f'{state.meipass}resources/start.ui')

    def load_fixed_drives(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        self.fixed_drives = []
        print(drives)
        for d in drives:
            drive_type = win32file.GetDriveType(d)
            if drive_type == win32file.DRIVE_FIXED or drive_type == win32file.DRIVE_REMOVABLE:
                label = win32api.GetVolumeInformation(d)[0]
                self.fixed_drives.append({"letter": d.replace("\\", ""), "label": label})

    def load_data_screen(self):
        self.ui_to_data()
        self.current_screen = "data"
        self.highlight_button(self.workflow_widget.dataButton)
        self.data_component.data_widget = self.load_main_frame(f'{state.meipass}resources/data.ui')

        self.data_component.load_data_screen(self.fixed_drives, self.aims_status_dialog, self.time_zone)

    def load_connect_screen(self):
        self.current_screen = "connect"
        self.connect_widget = self.load_main_frame(f'{state.meipass}resources/connect.ui')
        html = self.connect_widget.textBrowser.toHtml()
        html = html.replace("XXX_DIR_XXX", state.meipass2)
        self.connect_widget.textBrowser.setHtml(html)
        self.connect_widget.btnConnect.clicked.connect(self.connect)
        self.highlight_button(self.workflow_widget.connectButton)
        self.hint("Press the red connect button below")

    def load_connect_disks_screen(self):
        self.current_screen = "connect_disks"
        self.disk_drives_component.widget = self.load_main_frame(f'{state.meipass}resources/disk_drives.ui')
        self.highlight_button(self.workflow_widget.connectDisksButton)
        self.disk_drives_component.load_screen(self.fixed_drives, self.aims_status_dialog)

        self.disk_drives_component.widget.connectButton.clicked.connect(self.connect_disks)

    def connect_disks(self):
        self.drives_connected = self.disk_drives_component.connect()
        if self.drives_connected:
            self.load_connect_screen()

    def load_main_frame(self, ui_file):
        clearLayout(self.ui.mainFrame.layout())
        widget: QWidget = uic.loadUi(ui_file)
        self.ui.mainFrame.layout().addWidget(widget)
        return widget

    def connect(self):
        try:
            state.set_data_folders()
        except:
            raise Exception("Connect to the local disks first")

        data_loaded, message = state.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)
        if data_loaded:
            self.connect_widget.lblMessage.setText("Connected Successfully")
            if self.drives_connected:
                self.load_data_screen()
            state.reefscan_id = remove_control_characters(state.read_reefscan_id())
            self.camera_connected = True
            self.update_status()
        else:
            self.connect_widget.lblMessage.setText(message)

    def update_status(self):
        if state.model.local_data_loaded:
            self.archive_checker.check()
            bytes_available = self.archive_checker.archive_stats.space.actual_available_size
            gb_available = round(bytes_available / 1000000000)
            self.status_widget.lblDevice.setText(f"{state.reefscan_id}: {gb_available}  Gb Free")
            self.status_widget.lblSequences.setText(f"{len(state.model.camera_surveys)} sequences")
        else:
            self.status_widget.lblDevice.setText("camera not connected")
            self.status_widget.lblSequences.setText("camera not connected")

        self.load_fixed_drives()
        local_space = ""
        for drive in self.fixed_drives:
            du = shutil.disk_usage(drive["letter"])
            gbFree = round(du.free / 1000000000)
            local_space = local_space + f"{drive['letter']}({drive['label']}) {gbFree} Gb Free \n"
        self.status_widget.lblLocal.setText(local_space)

        # if self.current_screen == "data":
        #     self.load_data_screen()
        #
        if self.current_screen == "connect_disks":
            self.load_connect_disks_screen()

    def show(self):
        self.ui.show()



