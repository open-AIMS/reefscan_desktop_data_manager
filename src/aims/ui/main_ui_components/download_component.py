import logging
import os

from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QInputDialog

from aims import state
from aims.gui_model.tree_model import make_tree_model
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.ui.main_ui_components.utils import setup_folder_tree, setup_file_system_tree_and_combo_box, \
    update_data_folder_from_tree

logger = logging.getLogger(__name__)


class DownloadComponent:
    def __init__(self, main_ui):
        self.download_widget = None
        self.aims_status_dialog = None
        self.time_zone = None
        self.main_ui = main_ui

    def destination_drive_selected(self, value):
        print("combobox changed", value)
        setup_folder_tree(value, self.download_widget.destinationTree)

    def second_destination_drive_selected(self, value):
        print("combobox changed", value)
        setup_folder_tree(value, self.download_widget.secondDestinationTree)

    def load_download_screen(self, fixed_drives, time_zone, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone

        setup_file_system_tree_and_combo_box(drive_combo_box=self.download_widget.driveComboBox,
                                                  tree=self.download_widget.destinationTree,
                                                  selected_folder=state.config.data_folder,
                                             fixed_drives = fixed_drives)
        self.download_widget.driveComboBox.currentTextChanged.connect(self.destination_drive_selected)

        setup_file_system_tree_and_combo_box(drive_combo_box=self.download_widget.secondDriveComboBox,
                                                  tree=self.download_widget.secondDestinationTree,
                                                  selected_folder=state.config.backup_data_folder,
                                             fixed_drives = fixed_drives)
        self.download_widget.secondDriveComboBox.currentTextChanged.connect(self.second_destination_drive_selected)

        self.download_widget.cbBackup.setChecked(state.config.backup)

        self.download_widget.destinationTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.download_widget.destinationTree.customContextMenuRequested.connect(self.destination_tree_context_menu)

        self.download_widget.secondDestinationTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.download_widget.secondDestinationTree.customContextMenuRequested.connect(self.second_destination_tree_context_menu)

        self.setup_camera_tree()
        self.download_widget.downloadButton.clicked.connect(self.download)


    def download(self):
        state.config.backup = self.download_widget.cbBackup.isChecked()
        update_data_folder_from_tree(self.download_widget.destinationTree)

        if state.config.backup:
            selected = self.download_widget.secondDestinationTree.selectedIndexes()
            if len(selected) > 0:
                index = selected[0]
                item = self.download_widget.secondDestinationTree.model().filePath(index)
                state.config.backup_data_folder = str(item)
            else:
                raise Exception("Please select a backup folder")

        state.config.save_config_file()
        state.set_data_folders()

        surveys = self.checked_surveys()
        if len(surveys) == 0:
            raise Exception("Please select at least one survey")

        operation = SyncFromHardwareOperation(state.config.hardware_data_folder, state.config.data_folder, state.config.backup_data_folder, surveys, state.config.camera_samba)
        operation.update_interval = 1
        self.aims_status_dialog.set_operation_connections(operation)
        # # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.progress_dialog.close()

        state.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)
        self.setup_camera_tree()

        print("download done")

    def destination_tree_context_menu(self, position):
        create_folder_action = QAction("Create Folder")
        create_folder_action.triggered.connect(self.create_folder)
        menu = QMenu(self.download_widget.destinationTree)
        menu.addAction(create_folder_action)
        menu.exec_(self.download_widget.destinationTree.mapToGlobal(position))
        # the action executed when menu is clicked

    def create_folder(self):
        print ("create")
        selected = self.download_widget.destinationTree.selectedIndexes()
        if len(selected) > 0:
            index = selected[0]
            item = self.download_widget.destinationTree.model().filePath(index)
            parent_folder = str(item)
        else:
            parent_folder = self.download_widget.driveComboBox.currentText()

        new_folder, ok = QInputDialog.getText(self.main_ui, f'Create a new folder here {parent_folder}', f'Create new folder under {parent_folder} \n\nNew folder name:')
        if ok:
            os.makedirs(f"{parent_folder}/{new_folder}")

    def second_destination_tree_context_menu(self, position):
        create_folder_action = QAction("Create Folder")
        create_folder_action.triggered.connect(self.second_create_folder)
        menu = QMenu(self.download_widget.secondDestinationTree)
        menu.addAction(create_folder_action)
        menu.exec_(self.download_widget.secondDestinationTree.mapToGlobal(position))
        # the action executed when menu is clicked

    def second_create_folder(self):
        print ("create")
        selected = self.download_widget.secondDestinationTree.selectedIndexes()
        if len(selected) > 0:
            index = selected[0]
            item = self.download_widget.secondDestinationTree.model().filePath(index)
            parent_folder = str(item)
        else:
            parent_folder = self.download_widget.secondDriveComboBox.currentText()

        new_folder, ok = QInputDialog.getText(self.main_ui, f'Create a new folder here {parent_folder}', f'Create new folder under {parent_folder} \n\nNew folder name:')
        if ok:
            os.makedirs(f"{parent_folder}/{new_folder}")

    def setup_camera_tree(self):
        camera_tree = self.download_widget.cameraTree
        self.camera_model = make_tree_model(timezone=self.time_zone, include_local=False)
        camera_tree.setModel(self.camera_model)
        self.camera_model.itemChanged.connect(self.on_itemChanged)
        camera_tree.expandRecursively(self.camera_model.invisibleRootItem().index(), 3)

    # @pyqtSlot(QStandardItem)
    def on_itemChanged(self,  item):
        # print ("Item change")
        item.cascade_check()

    def checked_surveys(self, parent: QModelIndex = QModelIndex()):
        model = self.camera_model
        surveys = []
        for r in range(model.rowCount(parent)):
            index: QModelIndex = model.index(r, 0, parent)
            model_item = model.itemFromIndex(index)
            if model_item.isCheckable() and model_item.checkState() == Qt.Checked:
                survey_id = index.data(Qt.UserRole)
                if survey_id is not None:
                    surveys.append(survey_id)

            if model.hasChildren(index):
                child_surveys = self.checked_surveys(parent=index)
                surveys = surveys + child_surveys

        return surveys
