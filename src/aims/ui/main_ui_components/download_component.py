import logging
import os
from datetime import time
from time import process_time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QInputDialog, QDialog

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

    def load_download_screen(self, fixed_drives, time_zone, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone

        self.setup_camera_tree()
        self.download_widget.downloadButton.clicked.connect(self.download)


    def download(self):
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

        start = process_time()
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

        end = process_time()
        minutes = (end-start)/60
        print(f"Download Finished in {minutes} minutes")
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText("Download finished")
        errorbox.setDetailedText(f"Finished in {minutes} minutes")
        errorbox.exec_()

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
