import shutil

from PyQt5.QtWidgets import QMainWindow, QWidget, QTextBrowser
from PyQt5 import QtWidgets, uic, QtCore

from aims import data_loader
from aims.state import state
import sys
import logging
from PyQt5.QtCore import Qt

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.ui.main_ui_components.reefcloud_connect_component import ReefcloudConnectComponent
from aims2.operations2.archive_checker import ArchiveChecker
from aims.ui.main_ui_components.data_component import DataComponent
from aims.ui.main_ui_components.disk_drives_component import DiskDrivesComponent
from aims.ui.main_ui_components.upload_component import UploadComponent
from aims.ui.main_ui_components.utils import clearLayout
import win32file
import win32api
from tzlocal import get_localzone
import unicodedata
from aims.ui import deselectable_tree_view

logger = logging.getLogger("")


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


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

        if state.config.vietnemese:
            self.trans = QtCore.QTranslator(self)
            dir = f'{state.meipass}resources'
            print(dir)
            if self.trans.load('eng-vi', directory=dir):
                logger.info("translations loaded")
            else:
                logger.warn("translations not loaded")

            QtWidgets.QApplication.instance().installTranslator(self.trans)

        self.start_ui = f'{state.meipass}resources/main.ui'
        self.ui: QWidget = uic.loadUi(self.start_ui)

        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)

        self.data_component = DataComponent(hint_function=self.hint)
        self.upload_component = UploadComponent(hint_function=self.hint)
        self.disk_drives_component = DiskDrivesComponent(hint_function=self.hint)
        self.reefcloud_connect_component = ReefcloudConnectComponent(hint_function=self.hint)

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

        self.hint(self.tr('Choose "Connect Disks" from the workflow bar'))

    def hint(self, text):
        self.ui.hint_label.setText(text)

    def setup_timezone(self):
        localzone = get_localzone()
        self.time_zone = localzone

    def setup_status(self):
        status_widget_file = f'{state.meipass}resources/status_bar.ui'
        self.status_widget: QWidget = uic.loadUi(status_widget_file)
        self.ui.statusFrame.layout().addWidget(self.status_widget)
        self.status_widget.refreshButton.clicked.connect(self.update_status)

    def disable_all_workflow_buttons(self):
        self.workflow_widget.connectDisksButton.setEnabled(False)
        self.workflow_widget.connectButton.setEnabled(False)
        self.workflow_widget.dataButton.setEnabled(False)
        self.workflow_widget.connectReefcloudButton.setEnabled(False)
        self.workflow_widget.uploadButton.setEnabled(False)

    def highlight_button(self, button):
        self.enable_workflow_buttons()

        remove_button_border(self.workflow_widget.connectDisksButton)
        remove_button_border(self.workflow_widget.connectButton)
        remove_button_border(self.workflow_widget.dataButton)
        remove_button_border(self.workflow_widget.connectReefcloudButton)
        remove_button_border(self.workflow_widget.uploadButton)

        add_button_border(button)
        button.setEnabled(False)

    def enable_workflow_buttons(self):
        self.workflow_widget.connectDisksButton.setEnabled(True)
        self.workflow_widget.connectButton.setEnabled(self.drives_connected)
        self.workflow_widget.dataButton.setEnabled(self.drives_connected)
        self.workflow_widget.connectReefcloudButton.setEnabled(self.drives_connected)
        self.workflow_widget.uploadButton.setEnabled(
            self.drives_connected and self.reefcloud_connect_component.logged_in())

    def setup_workflow(self):
        workflow_widget_file = f'{state.meipass}resources/workflow_bar.ui'
        self.workflow_widget: QWidget = uic.loadUi(workflow_widget_file)
        self.ui.workflowFrame.layout().addWidget(self.workflow_widget)
        self.workflow_widget.connectButton.clicked.connect(self.load_connect_screen)
        self.workflow_widget.connectButton.setEnabled(False)
        self.workflow_widget.dataButton.setEnabled(False)
        self.workflow_widget.uploadButton.setEnabled(False)
        self.workflow_widget.connectReefcloudButton.setEnabled(False)
        self.workflow_widget.uploadButton.clicked.connect(self.load_upload_screen)
        self.workflow_widget.connectReefcloudButton.clicked.connect(self.load_reefcloud_connect_screen)
        self.workflow_widget.dataButton.clicked.connect(self.load_data_screen)
        self.workflow_widget.connectDisksButton.clicked.connect(self.load_connect_disks_screen)

    def ui_to_data(self):
        if self.current_screen == "data":
            self.data_component.check_save()

    def load_upload_screen(self):
        self.ui_to_data()
        self.current_screen = "upload"

        self.upload_component.upload_widget = self.load_main_frame(f'{state.meipass}resources/reefcloud-upload.ui')
        self.upload_component.load(aims_status_dialog=self.aims_status_dialog, time_zone=self.time_zone)
        self.highlight_button(self.workflow_widget.uploadButton)

    def load_reefcloud_connect_screen(self):
        self.ui_to_data()
        self.current_screen = "connect_reefcloud"

        self.reefcloud_connect_component.login_widget = self.load_main_frame(f'{state.meipass}resources/reefcloud-connect.ui')
        self.reefcloud_connect_component.load(aims_status_dialog=self.aims_status_dialog, time_zone=self.time_zone)
        self.reefcloud_connect_component.login_widget.login_button.clicked.connect(self.login_reefcloud)

        self.highlight_button(self.workflow_widget.connectReefcloudButton)

    def login_reefcloud(self):
        self.disable_all_workflow_buttons()
        if self.reefcloud_connect_component.login():
            self.load_data_screen()
        self.enable_workflow_buttons()

    def load_start_screen(self):
        widget = self.load_main_frame(f'{state.meipass}resources/start.ui')
        s1 = self.tr("To download and process images off the ReefScan System use the work flow in the left hand 'Workflow' bar.")
        s2 = self.tr("Click on 'Connect Disks' to first connect to your local disks.")
        s3 = self.tr("Click on 'Connect Camera' to connect to your reefscan camera.")
        s4 = self.tr("Click on 'Data' to download photos from the camera, browse your photos or edit metadata.")
        s5 = self.tr("Click on Reefcloud to upload your photos to reefcloud.")
        text_browser:QTextBrowser = widget.textBrowser
        html = text_browser.toHtml()
        html = html.replace("__s1__", s1)
        html = html.replace("__s2__", s2)
        html = html.replace("__s3__", s3)
        html = html.replace("__s4__", s4)
        html = html.replace("__s5__", s5)
        text_browser.setHtml(html)


    def load_fixed_drives(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        self.fixed_drives = []
        print(drives)
        for d in drives:
            drive_type = win32file.GetDriveType(d)
            if drive_type == win32file.DRIVE_FIXED or drive_type == win32file.DRIVE_REMOVABLE:
                try:
                    label = win32api.GetVolumeInformation(d)[0]
                except:
                    label = "Dont know"
                self.fixed_drives.append({"letter": d.replace("\\", ""), "label": label})

    def load_data_screen(self):
        self.ui_to_data()
        self.current_screen = "data"
        self.highlight_button(self.workflow_widget.dataButton)
        self.data_component.data_widget = self.load_main_frame(f'{state.meipass}resources/data.ui', package='aims.ui')

        self.data_component.load_data_screen(self.fixed_drives, self.aims_status_dialog, self.time_zone)

    def load_connect_screen(self):
        self.current_screen = "connect"
        self.connect_widget = self.load_main_frame(f'{state.meipass}resources/connect.ui')
        head = self.tr("Follow the Steps below to connect to the ReefScan Device:")

        s1 = self.tr("Plug an Ethernet cable from your Laptop or computer to the ReefScan device.")
        s2 = self.tr("Turn the ReefScan unit on via the power switch")
        s3 = self.tr("Wait until the ReefScan unit has started (about 5 minutes)")
        s4 = self.tr("Press the 'Connect' button below")

        html = self.connect_widget.textBrowser.toHtml()
        html = html.replace("XXX_DIR_XXX", state.meipass2)
        html = html.replace("__head__", head)
        html = html.replace("__s1__", s1)
        html = html.replace("__s2__", s2)
        html = html.replace("__s3__", s3)
        html = html.replace("__s4__", s4)
        self.connect_widget.textBrowser.setHtml(html)
        self.connect_widget.btnConnect.clicked.connect(self.connect)
        self.highlight_button(self.workflow_widget.connectButton)
        self.hint(self.tr("Press the red connect button below"))

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

    def load_main_frame(self, ui_file, package=None):
        clearLayout(self.ui.mainFrame.layout())
        widget: QWidget = uic.loadUi(ui_file, package=package)
        self.ui.mainFrame.layout().addWidget(widget)
        return widget

    def connect(self):
        try:
            state.set_data_folders()
        except:
            raise Exception("Connect to the local disks first")

        data_loaded, message = data_loader.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)
        if data_loaded:
            self.connect_widget.lblMessage.setText(self.tr("Connected Successfully"))
            if self.drives_connected:
                self.load_reefcloud_connect_screen()
            state.reefscan_id = remove_control_characters(state.read_reefscan_id())
            self.camera_connected = True
            self.update_status()
        else:
            self.connect_widget.lblMessage.setText(message)

    def update_status(self):
        if state.model.local_data_loaded:
            self.archive_checker.check()
            bytes_available = self.archive_checker.archive_stats.available_size()
            gb_available = round(bytes_available / 1000000000)
            self.status_widget.lblDevice.setText(f"{state.reefscan_id}: {gb_available}  " + self.tr("Gb Free"))
            self.status_widget.lblSequences.setText(f"{len(state.model.camera_surveys)} " + self.tr("sequences"))
        else:
            self.status_widget.lblDevice.setText(self.tr("camera not connected"))
            self.status_widget.lblSequences.setText(self.tr("camera not connected"))

        self.load_fixed_drives()
        local_space = ""
        try:
            for drive in self.fixed_drives:
                du = shutil.disk_usage(drive["letter"])
                gbFree = round(du.free / 1000000000)
                local_space = local_space + f"{drive['letter']}({drive['label']}) {gbFree} " + self.tr("Gb Free") + "\n"
        except:
            pass
        self.status_widget.lblLocal.setText(local_space)

        # if self.current_screen == "data":
        #     self.load_data_screen()
        #
        if self.current_screen == "connect_disks":
            self.load_connect_disks_screen()

    def show(self):
        if state.config.deep:
            self.ui.setWindowTitle("Reefscan Deep " + self.tr("Data Manager"))
        else:
            self.ui.setWindowTitle("Reefscan Transom " + self.tr("Data Manager"))

        if state.config.dev:
            self.ui.setWindowTitle(self.ui.windowTitle() + " - DEV")
        self.ui.show()



