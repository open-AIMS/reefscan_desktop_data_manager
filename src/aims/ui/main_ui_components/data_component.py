import time
from time import process_time
import logging

from reefscanner.basic_model.model_utils import print_time, replace_last

from aims.operations.add_reefcloud_site_operation import create_reefcloud_site_with_progress

logger = logging.getLogger("DataComponent")


start=process_time()

import datetime
import os
import shutil
import subprocess
import traceback
import typing

print_time("Imports done one", start, logger)

from PyQt5 import uic, QtWidgets, QtTest
from PyQt5.QtCore import QItemSelection, QSize, Qt, QObject
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QWidget, QTableView, QLabel, QListView, \
    QListWidget, QMessageBox, QTabWidget, QCheckBox, QHeaderView
from pytz import utc
from reefscanner.basic_model.exif_utils import get_exif_data
from reefscanner.basic_model.model_helper import rename_folders
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops
from reefscanner.basic_model.survey import Survey

print_time("Imports done two", start, logger)

from aims import data_loader
print_time("Imports done two.1", start, logger)
from aims import utils
print_time("Imports done two.2", start, logger)
from aims.state import state
print_time("Imports done two.3", start, logger)
from aims.gui_model.tree_model import TreeModelMaker, checked_survey_ids
print_time("Imports done two.5", start, logger)
from aims2.operations2.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.stats.survey_stats import SurveyStats
print_time("Imports done two.7", start, logger)
from aims.ui.main_ui_components.utils import clearLayout

from aims2.operations2.camera_utils import delete_archives
print_time("Imports done two.9", start, logger)
from aims2.reefcloud2.reefcloud_utils import create_reefcloud_site

import sys

print_time("Imports done three", start, logger)


"""
Check if code is run through a pyinstaller executable.
sys.frozen will be False if run through pyinstaller
otherwise if it is True then it indicates that it is
being run as a standalone script.

If the code is run through a pyinstaller we would want to 
disable the InferenceOperation and the related ChartOperation
due to file size requirements, i.e. tensorflow is required for
these operations but it is too large for the purposes
of a pyinstaller executable
"""
PYINSTALLER_COMPILED = getattr(sys, 'frozen', False)
if not PYINSTALLER_COMPILED:
    try:
        from aims.operations.inference_operation import InferenceOperation, inference_result_folder
        from aims.operations.chart_operation import ChartOperation
        from aims.ui.main_ui_components.cots_display_component import CotsDisplayComponent

    except Exception as e:
        logger.warn("Can't load inferencer", e)
        PYINSTALLER_COMPILED = True


def utc_to_local(utc_str, timezone):
    try:
        naive_date = datetime.datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S")
        utc_date = utc.localize(naive_date)
        local_date = utc_date.astimezone(timezone)
        return datetime.datetime.strftime(local_date, "%Y-%m-%d %H:%M:%S")
    except:
        return utc_str

print_time("Imports done", start, logger)


class DataComponent(QObject):
    def __init__(self, hint_function, disable_all_workflow_buttons, enable_workflow_buttons):
        start = process_time()
        super().__init__()
        self.data_widget = None
        self.metadata_widget = None
        self.info_widget = None
        self.marks_widget = None

        self.camera_model = None
        self.survey_id = None
        self.survey_list = None
        self.thumbnail_model = None

        self.marks_table: None
        self.mark_filename = None
        self.marks_model = None
        self.aims_status_dialog = None

        self.time_zone = None
        self.site_lookup = {}
        self.hint_function = hint_function
        # for long running processes we can disable the workflow buttons
        # and enable them when the process is complete
        self.disable_all_workflow_buttons = disable_all_workflow_buttons
        self.enable_workflow_buttons = enable_workflow_buttons

        self.clipboard: typing.Optional[Survey] = None
        self.current_tab = 2
        self.tree_collapsed = False
        self.cots_detector = None
        self.selected_index = None
        self.camera_tree_selected = False
        self.cots_display_component: CotsDisplayComponent = None
        self.map_component = None
        self.archive_data_loaded = False
        self.programatic_tab_changing = False

        print_time("Init done", start, logger)

    def tab_changed(self, index):

        if not self.programatic_tab_changing:
            logger.info(index)
            if index == self.get_index_by_tab_text(self.tr('Map')):
                from aims.ui.main_ui_components.map_component import MapComponent
                self.map_component = MapComponent(self.data_widget.map_tab, self.cots_display_params)
                surveys = self.get_all_descendants_as_surveys(self.selected_index)
                self.map_component.show(surveys)
            if index == self.get_index_by_tab_text(self.tr('COTS Photos')):
                self.cots_display_component.show()

    def copy(self):
        self.ui_to_data()
        self.clipboard = self.survey()

    def paste(self):
        if self.clipboard is not None:
            self.ui_to_data()
            if self.survey().site == "" or self.survey().site is None:
                self.survey().site = self.clipboard.site

            if self.survey().operator == "" or self.survey().operator is None:
                self.survey().operator = self.clipboard.operator

            if self.survey().observer == "" or self.survey().observer is None:
                self.survey().observer = self.clipboard.observer

            if self.survey().vessel == "" or self.survey().vessel is None:
                self.survey().vessel = self.clipboard.vessel

            if self.survey().tide == "" or self.survey().tide is None:
                self.survey().tide = self.clipboard.tide

            if self.survey().sea == "" or self.survey().sea is None:
                self.survey().sea = self.clipboard.sea

            if self.survey().wind == "" or self.survey().wind is None:
                self.survey().wind = self.clipboard.wind

            if self.survey().cloud == "" or self.survey().cloud is None:
                self.survey().cloud = self.clipboard.cloud

            if self.survey().visibility == "" or self.survey().visibility is None:
                self.survey().visibility = self.clipboard.visibility

            if self.survey().reefcloud_site == "" or self.survey().reefcloud_site is None:
                self.survey().reefcloud_site = self.clipboard.reefcloud_site

            if self.survey().reefcloud_project == "" or self.survey().reefcloud_project is None:
                self.survey().reefcloud_project = self.clipboard.reefcloud_project

            self.data_to_ui()
            self.ui_to_data()

    def load_data_screen(self, fixed_drives, aims_status_dialog, time_zone):

        self.archive_data_loaded = False
        self.time_zone = time_zone

        self.aims_status_dialog = aims_status_dialog

        self.info_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_info.ui',
                                                    self.data_widget.info_tab)
        self.metadata_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_metadata.ui',
                                                        self.data_widget.metadata_tab)
        self.marks_widget = self.load_sequence_frame(f'{state.meipass}resources/marks.ui',
                                                     self.data_widget.marks_tab)
        self.enhance_widget = self.load_sequence_frame(f'{state.meipass}resources/enhance.ui',
                                                       self.data_widget.enhance_tab)
        self.cots_display_widget = self.load_sequence_frame(f'{state.meipass}resources/cots_display.ui',
                                                            self.data_widget.cots_display_tab)

        self.eod_cots_widget = self.load_sequence_frame(f'{state.meipass}resources/eod_cots.ui',
                                                        self.data_widget.eod_cots_tab)
        self.inference_widget = self.load_sequence_frame(f'{state.meipass}resources/inference.ui',
                                                         self.data_widget.inference_tab)

        self.info_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_info.ui',
                                                    self.data_widget.info_tab)
        self.metadata_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_metadata.ui',
                                                        self.data_widget.metadata_tab)
        self.marks_widget = self.load_sequence_frame(f'{state.meipass}resources/marks.ui',
                                                     self.data_widget.marks_tab)

        self.lookups()
        self.data_widget.renameFoldersButton.clicked.connect(self.rename_folders)
        self.data_widget.refreshButton.clicked.connect(self.refresh)

        self.marks_widget.btnOpenMarkFolder.clicked.connect(self.open_mark_folder)
        self.marks_widget.btnOpenMark.clicked.connect(self.open_mark)
        self.data_widget.open_folder_button.clicked.connect(self.open_folder)
        self.data_widget.tabWidget.setCurrentIndex(0)
        self.data_widget.tabWidget.setEnabled(False)
        self.survey_id = None
        self.metadata_widget.cancelButton.clicked.connect(self.data_to_ui)
        self.metadata_widget.saveButton.clicked.connect(self.ui_to_data)
        self.metadata_widget.newSiteButton.clicked.connect(self.add_new_reefcloud_site)
        self.metadata_widget.btn_copy.clicked.connect(self.copy)
        self.metadata_widget.btn_paste.clicked.connect(self.paste)

        self.load_explore_surveys_tree()

        self.data_widget.downloadButton.clicked.connect(self.download)
        self.data_widget.showDownloadedCheckBox.stateChanged.connect(self.show_downloaded_changed)
        self.data_widget.deleteDownloadedButton.clicked.connect(self.delete_downloaded)
        self.data_widget.collapseTreeButton.clicked.connect(self.collapseTrees)

        if self.setup_camera_tree():
            self.data_widget.camera_not_connected_label.setVisible(False)
            self.data_widget.camera_panel.setVisible(True)
            self.data_widget.extra_operations_widget.setVisible(not PYINSTALLER_COMPILED)
        else:
            self.data_widget.camera_not_connected_label.setVisible(True)
            self.data_widget.camera_panel.setVisible(False)

        self.initial_disables()
        self.set_hint()

        self.enhance_widget.btnEnhanceOpenFolder.clicked.connect(self.enhance_open_folder)
        self.enhance_widget.btnEnhanceFolder.clicked.connect(self.enhance_photos)

        self.enhance_widget.textEditCPULoad.setPlainText("0.8")
        self.enhance_widget.checkBoxDisableDenoising.setChecked(False)
        self.enhance_widget.checkBoxDisableDehazing.setChecked(False)

        self.inference_widget.btnInferenceOpenFolder.clicked.connect(self.inference_open_folder)
        self.inference_widget.btnInferenceFolder.clicked.connect(self.inference)

        if PYINSTALLER_COMPILED:
            self.remove_tab_by_tab_text(self.tr('Inference'))
            self.remove_tab_by_tab_text(self.tr('Chart'))
            self.remove_tab_by_tab_text(self.tr('End-Of-Day-COTS'))
            self.remove_tab_by_tab_text(self.tr('COTS Photos'))
            self.cots_display_params = None
        else:
            self.eod_cots_widget.detectCotsButton.clicked.connect(self.detect_cots)
            self.eod_cots_widget.cancelButton.clicked.connect(self.cancel_detect)
            from aims2.operations2.cots_detector import CotsDetector
            self.cots_detector = CotsDetector(output=self.eod_cots_widget.detectorOutput,
                                              parent=self
                                              )
            from aims.model.cots_display_params import CotsDisplayParams
            self.cots_display_params = CotsDisplayParams()
            self.cots_display_component = CotsDisplayComponent(self.cots_display_widget, self.cots_display_params)

        self.data_widget.tabWidget.currentChanged.connect(self.tab_changed)


    def get_index_by_tab_text(self, name_of_tab):
        for i in range(self.data_widget.tabWidget.count()):
            if self.data_widget.tabWidget.tabText(i) == name_of_tab:
                return i

    def hide_tab_by_tab_text(self, name_of_tab):
        index = self.get_index_by_tab_text(name_of_tab)
        self.data_widget.tabWidget.setTabEnabled(index, False)

    def remove_tab_by_tab_text(self, name_of_tab):
        index = self.get_index_by_tab_text(name_of_tab)
        self.data_widget.tabWidget.removeTab(index)

    def show_tab_by_tab_text(self, name_of_tab):
        index = self.get_index_by_tab_text(name_of_tab)
        self.data_widget.tabWidget.setTabEnabled(index, True)


    def display_cots_detections(self, samba):
        if self.survey() is None:
            return

        if self.cots_display_params is not None:
            self.cots_display_params.read_data(self.survey().folder, samba)

    def detect_cots(self):
        survey_infos = self.get_all_descendants(self.selected_index)
        self.detect_cots_for_surveys(survey_infos)

    def detect_cots_for_surveys(self, survey_infos):
        self.disable_everything()
        self.eod_cots_widget.detectCotsButton.setEnabled(False)
        self.eod_cots_widget.cancelButton.setEnabled(True)
        try:
            for survey_info in survey_infos:
                survey = state.model.surveys_data[survey_info["survey_id"]]
                self.cots_detector.callProgram(survey.folder)
                while not self.cots_detector.batch_result.finished:
                    QApplication.processEvents()
                self.cots_display_params.cots_detection_list().read_eod_files(
                        f"{survey.folder}", samba=False, use_cache=False)

            if self.cots_detector.batch_result.finished:
                self.enable_everything()
                return
        finally:
            self.enable_everything()
            self.eod_cots_widget.detectCotsButton.setEnabled(True)
            self.eod_cots_widget.cancelButton.setEnabled(False)

    def cancel_detect(self):
        logger.info("cancelled detector")
        self.cots_detector.cancel()

    def collapseTrees(self):
        self.tree_collapsed = not self.tree_collapsed
        self.data_widget.treesWidget.setVisible(not self.tree_collapsed)
        if self.tree_collapsed:
            self.data_widget.collapseTreeButton.setText(">>")
        else:
            self.data_widget.collapseTreeButton.setText("<<")

    def add_new_reefcloud_site(self):
        project = self.metadata_widget.cb_reefcloud_project.currentText()
        site = self.metadata_widget.ed_site.text()

        all_sites = [self.metadata_widget.cb_reefcloud_site.itemText(i) for i in
                     range(self.metadata_widget.cb_reefcloud_site.count())]
        logger.info(all_sites)

        if site in all_sites:
            raise Exception(f"{site} already exists. Choose it from the drop down.")

        if project is None or project == "":
            raise Exception("Choose a reefcloud project first.")

        if site is None or site == "":
            raise Exception("Enter a site name in the site field.")

        if state.reefcloud_session is None:
            raise Exception("Log on to reefcloud first. (See the reefcloud tab)")

        site_id = create_reefcloud_site_with_progress(project, site, self.survey(), self.aims_status_dialog)

        self.update_sites_combo()
        self.metadata_widget.cb_reefcloud_site.setCurrentText(site)

        self.site_lookup[site_id] = site
        self.metadata_widget.cb_reefcloud_site.addItem(site, site_id)
        message_box = QtWidgets.QMessageBox()
        message_box.setText(self.tr("Site created with default properties"))
        message_box.setDetailedText("You can modify the site properties in reefcloud")
        message_box.exec_()

    def disable_save_cancel(self):
        self.metadata_widget.saveButton.setEnabled(False)
        self.metadata_widget.cancelButton.setEnabled(False)
        self.metadata_widget.ed_site.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_operator.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_operator.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_observer.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_vessel.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_sea.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_wind.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_cloud.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_vis.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_comments.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_tide.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.ed_name.textChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_reefcloud_project.currentTextChanged.connect(self.enable_save_cancel)
        self.metadata_widget.cb_reefcloud_site.currentTextChanged.connect(self.enable_save_cancel)

    def enable_save_cancel(self):
        self.metadata_widget.saveButton.setEnabled(True)
        self.metadata_widget.cancelButton.setEnabled(True)

    def initial_disables(self):
        self.disable_all_tabs(0)
        self.data_widget.downloadButton.setEnabled(False)
        self.data_widget.deleteDownloadedButton.setEnabled(False)
        self.data_widget.showDownloadedCheckBox.setChecked(False)
        self.data_widget.showDownloadedCheckBox.setEnabled(len(state.model.archived_surveys) > 0)

    def show_downloaded_changed(self):
        if self.setup_camera_tree():
            self.data_widget.deleteDownloadedButton.setEnabled(self.data_widget.showDownloadedCheckBox.isChecked())

    def delete_downloaded(self):
        msgBox = QMessageBox()
        msgBox.setText(self.tr("Are you sure you want to delete the downloaded surveys from the camera?"))
        msgBox.setWindowTitle(self.tr('Delete?'))
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        msgBox.button(QMessageBox.Yes).setText(self.tr("Yes"))
        msgBox.button(QMessageBox.No).setText(self.tr("No"))

        reply = msgBox.exec()

        if reply == QMessageBox.Yes:
            delete_archives(state.config.camera_ip)

        state.model.archived_data_loaded = False
        self.setup_camera_tree()

    def download(self):
        self.check_save()
        self.survey_id = None
        self.data_widget.surveysTree.selectionModel().clearSelection()
        self.data_widget.cameraTree.selectionModel().clearSelection()

        start = process_time()
        surveys = checked_survey_ids(self.camera_model)

        if len(surveys) == 0:
            raise Exception("Please select at least one survey")

        operation = SyncFromHardwareOperation(state.config.hardware_data_folder, state.primary_folder,
                                              state.backup_folder, surveys, state.config.camera_samba)
        operation.update_interval = 1
        self.aims_status_dialog.set_operation_connections(operation)
        # # operation.after_run.connect(self.after_sync)

        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        while not result.ready():
            QApplication.processEvents()
        self.aims_status_dialog.close()

        data_loader.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)
        self.archive_data_loaded = False

        state.model.archived_data_loaded = False
        self.setup_camera_tree()
        self.load_explore_surveys_tree()

        download_end = process_time()

        find_cots_check_box: QCheckBox = self.data_widget.find_cots_check_box
        inference_check_box: QCheckBox = self.data_widget.inference_check_box
        enhance_check_box: QCheckBox = self.data_widget.enhance_check_box

        if find_cots_check_box.checkState() == Qt.Checked:
            self.data_widget.tabWidget.setCurrentIndex(8)
            self.detect_cots_for_surveys(surveys)

        cots_end = process_time()

        if inference_check_box.checkState() == Qt.Checked:
            self.inference_surveys(surveys, replace=False)
        inference_end = process_time()

        if enhance_check_box.checkState() == Qt.Checked:
            self.enhance_photos_for_surveys(surveys, disable_denoising=True, disable_dehazing=True, replace=False)
        enhance_end = process_time()

        download_minutes = (download_end - start) / 60
        logger.info(f"Download Finished in {download_minutes} minutes")

        cots_minutes = (cots_end - download_end) / 60
        cots_text = f"COTS detect Finished in {cots_minutes} minutes"
        logger.info(cots_text)

        inference_minutes = (inference_end - cots_end) / 60
        inference_text = f"Inference Finished in {inference_minutes} minutes"
        logger.info(inference_text)

        enhance_minutes = (enhance_end - inference_end) / 60
        enhance_text = f"Enhance Finished in {enhance_minutes} minutes"
        logger.info(enhance_text)

        if self.cots_display_component is not None:
            for survey_info in surveys:
                survey = state.model.surveys_data[survey_info["survey_id"]]
                self.cots_display_params.cots_detection_list().read_realtime_files(survey.folder, samba=False, use_cache=False)

        self.initial_disables()

        errorbox = QtWidgets.QMessageBox()
        errorbox.setText(self.tr("Download finished"))
        errorbox.setDetailedText(self.tr("Finished in ") + str(download_minutes) + self.tr(" minutes") + "\n"
                                 + cots_text + "\n" + inference_text + "\n" + enhance_text + "\n"
                                 )
        errorbox.setWindowTitle("ReefScan")
        self.aims_status_dialog.progress_dialog.close()
        errorbox.exec_()

    def setup_camera_tree(self):
        if state.model.camera_data_loaded:
            show_downloaded = self.data_widget.showDownloadedCheckBox.isChecked()
            if not self.archive_data_loaded:
                data_loader.load_archive_data_model(aims_status_dialog=self.aims_status_dialog)
                self.archive_data_loaded = True

            camera_tree = self.data_widget.cameraTree
            self.camera_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_local=False,
                                                                 include_archives=show_downloaded, checkable=True)
            camera_tree.setModel(self.camera_model)
            self.camera_model.itemChanged.connect(self.camera_on_itemChanged)
            self.data_widget.cameraTree.selectionModel().selectionChanged.connect(self.camera_tree_selection_changed)
            camera_tree.expandRecursively(self.camera_model.invisibleRootItem().index(), 3)
            return True
        else:
            return False

    def camera_on_itemChanged(self, item):
        # print ("Item change")
        item.cascade_check()
        surveys = checked_survey_ids(self.camera_model)
        self.data_widget.downloadButton.setEnabled(len(surveys) > 0)
        self.set_hint()

    def lookups(self):

        self.metadata_widget.cb_tide.addItem("", userData="")
        self.metadata_widget.cb_tide.addItem(self.tr("falling"), userData="falling")
        self.metadata_widget.cb_tide.addItem(self.tr("high"), userData="high")
        self.metadata_widget.cb_tide.addItem(self.tr("low"), userData="low")
        self.metadata_widget.cb_tide.addItem(self.tr("rising"), userData="rising")

        self.metadata_widget.cb_sea.addItem("", userData="")
        self.metadata_widget.cb_sea.addItem(self.tr("calm"), userData="calm")
        self.metadata_widget.cb_sea.addItem(self.tr("slight"), userData="slight")
        self.metadata_widget.cb_sea.addItem(self.tr("moderate"), userData="moderate")
        self.metadata_widget.cb_sea.addItem(self.tr("rough"), userData="rough")

        self.metadata_widget.cb_wind.addItem("")
        self.metadata_widget.cb_wind.addItem("<5")
        self.metadata_widget.cb_wind.addItem("5-10")
        self.metadata_widget.cb_wind.addItem("10-15")
        self.metadata_widget.cb_wind.addItem("15-20")
        self.metadata_widget.cb_wind.addItem("20-25")
        self.metadata_widget.cb_wind.addItem("25-30")
        self.metadata_widget.cb_wind.addItem(">30")

        self.metadata_widget.cb_cloud.addItem("")
        self.metadata_widget.cb_cloud.addItem("0")
        self.metadata_widget.cb_cloud.addItem("1")
        self.metadata_widget.cb_cloud.addItem("2")
        self.metadata_widget.cb_cloud.addItem("3")
        self.metadata_widget.cb_cloud.addItem("4")
        self.metadata_widget.cb_cloud.addItem("5")
        self.metadata_widget.cb_cloud.addItem("6")
        self.metadata_widget.cb_cloud.addItem("7")
        self.metadata_widget.cb_cloud.addItem("8")

        self.metadata_widget.cb_vis.addItem("")
        self.metadata_widget.cb_vis.addItem("<5")
        self.metadata_widget.cb_vis.addItem("5-10")
        self.metadata_widget.cb_vis.addItem("10-15")
        self.metadata_widget.cb_vis.addItem("15-20")
        self.metadata_widget.cb_vis.addItem("20-25")
        self.metadata_widget.cb_vis.addItem("25-30")
        self.metadata_widget.cb_vis.addItem(">30")

        self.metadata_widget.cb_reefcloud_project.addItem("")
        self.project_lookups=[]
        for project in state.config.reefcloud_projects:
            self.metadata_widget.cb_reefcloud_project.addItem(project)
            self.project_lookups.append(project)

        self.metadata_widget.cb_reefcloud_site.addItem("", userData="")

        self.metadata_widget.cb_reefcloud_project.currentIndexChanged.connect(self.cb_reefcloud_project_changed)

    def cb_reefcloud_project_changed(self, index):
        self.update_sites_combo()

    def update_sites_combo(self):
        # figure out what project was selected.
        project:str = self.metadata_widget.cb_reefcloud_project.currentText()
        if project == "" or project.endswith("Permission Denied"):
            # No project was selected, site not meaningful.
            # Valid sites are set on per project basis.
            self.metadata_widget.cb_reefcloud_site.clear()
            self.metadata_widget.cb_reefcloud_site.addItem("")
            self.metadata_widget.cb_reefcloud_site.setCurrentText("")
            self.metadata_widget.cb_reefcloud_site.setEnabled(False)
        else:
            # If it is not "", enable sites combo.
            self.metadata_widget.cb_reefcloud_site.setEnabled(True)
            # Clear old options
            self.metadata_widget.cb_reefcloud_site.clear()
            self.metadata_widget.cb_reefcloud_site.addItem("", userData="")
            # Add sites for that project to the sites combo box
            sites = state.config.reefcloud_sites[project]
            for site in sites:
                self.metadata_widget.cb_reefcloud_site.addItem(site["name"], userData=site["id"])
                self.site_lookup[site["id"]] = site["name"]

    def rename_folders(self):
        if not state.read_only:
            self.check_save()
            old_survey_id = self.survey_id
            self.survey_id = None
            try:
                rename_folders(state.model, self.time_zone)
            except Exception as e:
                traceback.print_exc()
                raise Exception("Error renaming folders. Maybe you have a file or folder open in another window.")

            self.load_explore_surveys_tree()
            self.setup_camera_tree()
            self.survey_id = old_survey_id
            self.data_to_ui()

            logger.info("rename done")

    def refresh(self):
        self.check_save()
        old_survey_id = self.survey_id
        self.survey_id = None
        self.load_explore_surveys_tree()
        self.setup_camera_tree()
        self.survey_id = old_survey_id
        self.data_to_ui()
        logger.info("refresh done")

    def load_sequence_frame(self, ui_file, parent_widget):
        clearLayout(parent_widget.layout())
        widget: QWidget = uic.loadUi(ui_file)
        parent_widget.layout().addWidget(widget)
        return widget

    def load_marks(self):
        from aims.gui_model.marks_model import MarksModel

        self.marks_table: QTableView = self.marks_widget.tableView
        self.mark_filename = None
        self.marks_model = MarksModel(self.survey().folder)
        self.marks_table.setModel(self.marks_model)
        self.marks_table.selectionModel().currentChanged.connect(self.marks_table_clicked)
        if self.marks_model.hasData():
            self.marks_table.selectRow(0)
        else:
            label: QLabel = self.marks_widget.lblPhoto
            label.clear()
            self.marks_widget.lblFileName.setText(self.tr("There are no marks for this sequence"))

    def marks_table_clicked(self, selected, deselected):
        index = selected
        if self.marks_model is not None:
            self.mark_filename = self.marks_model.photo_file(index.row())
            self.marks_widget.lblFileName.setText(self.marks_model.photo_file_name(index.row()))
            label: QLabel = self.marks_widget.lblPhoto
            pixmap = QPixmap(self.mark_filename).scaled(label.size().width(), label.size().height(), Qt.KeepAspectRatio,
                                                        Qt.SmoothTransformation)
            label.setPixmap(pixmap)

    def open_folder(self):
        utils.open_file(self.survey().folder)

    def open_mark(self):
        if self.mark_filename is not None:
            utils.open_file(self.mark_filename)

    def open_mark_folder(self):
        if self.mark_filename is not None:
            try:
                fname = self.mark_filename.replace("//", "/")
                fname = fname.replace("/", "\\")
                command = f'explorer.exe /select,"{fname}"'
                # logger.info(command)
                subprocess.call(command)
            except:
                utils.open_file(self.mark_filename, "open")

    def enhanced_folder(self, survey):
        return replace_last(survey, "/reefscan/", "/reefscan_enhanced/")

    def enhance_open_folder(self):
        utils.open_file(self.enhanced_folder(self.survey().folder))

    # enhance all of the photos for the currently selected survey
    # if a folder is selected do it for all descendant surveys of that folder
    def enhance_photos(self):
        # if a specific survey is selected then we replace existing (which currently just means redo the sub-sampling)
        logger.info(f"start enhance {process_time()}")
        replace = self.survey() is not None

        survey_infos = self.get_all_descendants(self.selected_index)
        disable_denoising = self.enhance_widget.checkBoxDisableDenoising.isChecked()
        disable_dehazing = self.enhance_widget.checkBoxDisableDehazing.isChecked()

        self.enhance_photos_for_surveys(survey_infos, disable_denoising=disable_denoising,
                                        disable_dehazing=disable_dehazing, replace=replace)

    def enhance_photos_for_surveys(self, survey_infos, disable_denoising=True, disable_dehazing=True, replace=False):
        logger.info(f"start enhance_photos_for_surveys {process_time()}")
        self.disable_everything()
        self.enhance_widget.btnEnhanceFolder.setEnabled(False)
        try:
            for survey_info in survey_infos:
                survey = state.model.surveys_data[survey_info["survey_id"]]
                result = self.enhance_photos_for_survey(survey, disable_denoising=disable_denoising,
                                                        disable_dehazing=disable_dehazing, replace=replace)
                if not result:
                    self.enable_everything()
                    return
        finally:
            self.enable_everything()
            self.enhance_widget.btnEnhanceFolder.setEnabled(True)
            self.enhance_widget.btnEnhanceOpenFolder.setVisible(True)

    # enhance all of the photos for one survey
    # returns true if successful false otherwise
    def enhance_photos_for_survey(self, survey, disable_denoising=True,
                                  disable_dehazing=True, replace=False) -> bool:
        logger.info(f"start enhance_photos_for_survey {process_time()}")

        subsampled_image_folder = replace_last(survey.folder, "/reefscan/", "/reefscan_reefcloud/")
        if replace or utils.is_empty_folder(subsampled_image_folder):
            from aims.operations.load_data import reefcloud_subsample

            success, selected_photo_infos = reefcloud_subsample(survey.folder, subsampled_image_folder,
                                                                self.aims_status_dialog)
            if not success:
                self.aims_status_dialog.close()
                return False

        output_suffix = "_enh"
        output_folder = self.enhanced_folder(survey.folder)
        # output_suffix = self.enhance_widget.textEditSuffix.toPlainText()
        cpu_load_string = self.enhance_widget.textEditCPULoad.toPlainText()
        if not disable_denoising:
            output_suffix = output_suffix + "_denoise"
        if not disable_dehazing:
            output_suffix = output_suffix + "_dehaze"

        self.enhance_widget.textBrowser.append("Photoenhancer starting")
        self.enhance_widget.textBrowser.append(f"Enhanced photos will be saved in the folder \'{output_folder}\'")
        if self.enhance_widget.checkBoxDisableDenoising.isChecked():
            self.enhance_widget.textBrowser.append("Denoising step is skipped for faster performance.")
        if self.enhance_widget.checkBoxDisableDehazing.isChecked():
            self.enhance_widget.textBrowser.append("Dehazing step is skipped for faster performance.")

        QApplication.processEvents()

        from aims.operations.enhance_photo_operation import EnhancePhotoOperation

        enhance_operation = EnhancePhotoOperation(target=subsampled_image_folder,
                                                  load=float(cpu_load_string),
                                                  suffix=output_suffix,
                                                  output_folder=output_folder,
                                                  disable_denoising=disable_denoising,
                                                  disable_dehazing=disable_dehazing)

        enhance_operation.update_interval = 1
        self.aims_status_dialog.set_operation_connections(enhance_operation)
        enhance_operation.set_msg_function(lambda msg: self.enhance_widget.textBrowser.append(msg))
        # # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(enhance_operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.close()

        if enhance_operation.batch_monitor.finished:
            self.enhance_widget.textBrowser.append("Photoenhancer finished")
        else:
            if enhance_operation.batch_monitor.cancelled:
                self.enhance_widget.textBrowser.append("Photoenhancer was cancelled")

        return not enhance_operation.batch_monitor.cancelled

    def enable_everything(self):
        self.enable_workflow_buttons()
        self.enable_tabs()
        self.data_widget.treesWidget.setEnabled(True)

    def disable_everything(self):
        current_tab = self.data_widget.tabWidget.currentIndex()
        self.disable_all_workflow_buttons()
        self.disable_all_tabs(current_tab)
        self.data_widget.treesWidget.setEnabled(False)

    def load_inference_charts(self):
        if self.survey() is not None:
            if not PYINSTALLER_COMPILED:
                coverage_results_file = f"{inference_result_folder(self.survey().folder)}/coverage.csv"
                if os.path.exists(coverage_results_file):
                    self.show_tab_by_tab_text(self.tr('Chart'))

                    self.chart_widget = self.load_sequence_frame(f'{state.meipass}resources/chart.ui',
                                                                 self.data_widget.chart_tab)
                    self.chart_widget = self.load_sequence_frame(f'{state.meipass}resources/chart.ui',
                                                                self.data_widget.chart_tab)

                    pie_browser = QWebEngineView(self.chart_widget.pieChartWidget)

                    vlayout = QtWidgets.QVBoxLayout(self.chart_widget.pieChartWidget)
                    vlayout.addWidget(pie_browser)

                    chart_operation = ChartOperation()
                    fig = chart_operation.create_pie_chart_benthic_groups(coverage_results_file)
                    pie_browser.setHtml(fig)
                else:
                    self.hide_tab_by_tab_text(self.tr('Chart'))

    def inference_open_folder(self):
        utils.open_file(inference_result_folder(self.survey().folder))

    # inference all of the photos for the currently selected survey
    # if a folder is selected do it for all descendant surveys of that folder
    def inference(self):
        # if a specific survey is selected then we replace existing (which currently just means redo the sub-sampling)
        replace = self.survey() is not None
        survey_infos = self.get_all_descendants(self.selected_index)
        self.inference_surveys(survey_infos, replace)

    def inference_surveys(self, survey_infos, replace):
        try:
            self.disable_everything()
            for survey_info in survey_infos:
                survey = state.model.surveys_data[survey_info["survey_id"]]
                result = self.inference_survey(survey, replace=replace)
                if not result:
                    self.enable_everything()
                    return
        finally:
            self.enable_everything()

    # enhance all of the photos for one survey
    # returns an object with information as to the successful completion
    # of the operation

    def inference_survey(self, survey: Survey, replace = False) -> bool:
        subsampled_image_folder = replace_last(survey.folder, "/reefscan/", "/reefscan_reefcloud/")
        output_folder = inference_result_folder(survey.folder)

        if replace or utils.is_empty_folder(subsampled_image_folder):
            from aims.operations.load_data import reefcloud_subsample
            success, selected_photo_infos = reefcloud_subsample(survey.folder, subsampled_image_folder,
                                                            self.aims_status_dialog)
            if not success:
                self.aims_status_dialog.close()
                raise Exception (f"Error subsampling photos for survey {survey.best_name()}")

        if utils.is_empty_folder(subsampled_image_folder):
            raise Exception(f"No photos to inference in {subsampled_image_folder}")

        # output_folder = self.inference_widget.textEditOutputFolder.toPlainText() if self.inference_widget.checkBoxOutputFolder.isChecked() else 'inference_results'

        if replace or utils.is_empty_folder(output_folder):

            self.inference_widget.textBrowser.append(f"Inferencer starting for {survey.best_name()}")

            QApplication.processEvents()

            inference_operation = InferenceOperation(target=subsampled_image_folder, results_folder=output_folder)

            inference_operation.update_interval = 1
            self.aims_status_dialog.set_operation_connections(inference_operation)
            inference_operation.set_msg_function(lambda msg: self.inference_widget.textBrowser.append(msg))
            # # operation.after_run.connect(self.after_sync)
            logger.info("done connections")
            result = self.aims_status_dialog.threadPool.apply_async(inference_operation.run)
            logger.info("thread started")
            while not result.ready():
                QApplication.processEvents()
            logger.info("thread finished")
            self.aims_status_dialog.close()

            if inference_operation.batch_monitor.cancelled:
                self.inference_widget.textBrowser.append("Inferencer was cancelled")
            else:
                self.inference_widget.textBrowser.append("Inferencer finished")

            coverage_file = f"{output_folder}/coverage.csv"
            self.inference_widget.textBrowser.append(f'Pie Chart from {coverage_file}')
            self.load_inference_charts()
            return not inference_operation.batch_monitor.cancelled
        else:
            return True

    def camera_tree_selection_changed(self, item_selection: QItemSelection):
        self.metadata_widget.newSiteButton.setVisible(False)
        self.camera_tree_selected = True

        logger.info("camera tree changed")
        self.check_save()
        if self.data_widget.surveysTree.selectionModel() is not None:
            self.data_widget.surveysTree.selectionModel().blockSignals(True)
            self.data_widget.surveysTree.selectionModel().clearSelection()
            self.data_widget.surveysTree.selectionModel().blockSignals(False)
        if len(item_selection.indexes()) == 0:
            return ()

        self.selected_index = self.find_selected_tree_index(item_selection)
        self.set_survey_id_and_list_from_selected_index()

        # logger.info(f"survey_id {self.survey_id}")
        # logger.info(f"survey {self.survey()}")

        self.enable_tabs()

        self.data_to_ui()
        self.display_cots_detections(samba=True)
        self.tab_changed(self.read_current_tab())

        self.set_hint()

    def set_survey_id_and_list_from_selected_index(self):
        selected_index_data = self.selected_index.data(Qt.UserRole)
        if selected_index_data == None:
            self.survey_id = None
            self.survey_list = None
        else:
            self.survey_id = selected_index_data["survey_id"]
            if selected_index_data["branch"] == self.tr("New Sequences"):
                self.survey_list = state.model.camera_surveys
            elif selected_index_data["branch"] == self.tr("Downloaded Sequences"):
                self.survey_list = state.model.archived_surveys
            else:
                self.survey_list = state.model.surveys_data

    # Based on the current state this method will enable the appropriate tabs
    def enable_tabs(self):
        self.programatic_tab_changing = True
        if self.data_widget.tabWidget.currentIndex() != 0:
            self.current_tab = self.read_current_tab()
        if self.camera_tree_selected:
            if self.survey_id is None:
                self.disable_all_tabs(0)
            else:
                self.enable_metadata_tab_only()
        else:
            if self.survey_id is None:
                self.enable_processing_tabs_only()
            else:
                self.enable_all_tabs()

        self.programatic_tab_changing = False
        if self.data_widget.tabWidget.isTabEnabled(self.current_tab):
            self.data_widget.tabWidget.setCurrentIndex(self.current_tab)

# show the metadata_tab, the map tab and the COTS photos tab
    def enable_metadata_tab_only(self):
        self.programatic_tab_changing = True

        self.disable_all_tabs(None)
        self.data_widget.tabWidget.setEnabled(True)
        self.data_widget.tabWidget.setTabEnabled(2, True)
        self.data_widget.tabWidget.setTabEnabled(9, True)
        self.programatic_tab_changing = False

        if self.data_widget.tabWidget.currentIndex() not in [2, 3, 9]:
            self.data_widget.tabWidget.setCurrentIndex(2)

    def read_current_tab(self):
        return self.data_widget.tabWidget.currentIndex()

    def enable_processing_tabs_only(self):
        self.programatic_tab_changing = True
        self.disable_all_tabs(None)
        self.data_widget.tabWidget.setEnabled(True)
        self.data_widget.tabWidget.setTabEnabled(1, True)
        self.data_widget.tabWidget.setTabEnabled(3, True)
        self.data_widget.tabWidget.setTabEnabled(6, True)
        self.data_widget.tabWidget.setTabEnabled(7, True)
        self.data_widget.tabWidget.setTabEnabled(8, True)
        self.programatic_tab_changing = False
        if self.data_widget.tabWidget.currentIndex() not in [1, 6, 7, 8]:
            self.data_widget.tabWidget.setCurrentIndex(1)

    def disable_all_tabs(self, index):
        self.programatic_tab_changing = True
        tab_widget: QTabWidget = self.data_widget.tabWidget
        tabs_count = tab_widget.count()
        for i in range(tabs_count + 1):
            self.data_widget.tabWidget.setTabEnabled(i, False)

        self.programatic_tab_changing = False
        if index is not None:
            self.data_widget.tabWidget.setTabEnabled(index, True)
            tab_widget.setCurrentIndex(index)

    def enable_all_tabs(self):
        self.programatic_tab_changing = True

        tab_widget: QTabWidget = self.data_widget.tabWidget
        tabs_count = tab_widget.count()
        tab_widget.setEnabled(True)
        for i in range(tabs_count + 1):
            self.data_widget.tabWidget.setTabEnabled(i, True)
        self.programatic_tab_changing = False

    def explore_tree_selection_changed(self, item_selection: QItemSelection):
        self.camera_tree_selected = False
        self.metadata_widget.newSiteButton.setVisible(True)
        if self.data_widget.tabWidget.isEnabled():
            self.current_tab = self.read_current_tab()

        logger.info("local tree changed")
        self.check_save()
        if self.data_widget.cameraTree.selectionModel() is not None:
            self.data_widget.cameraTree.selectionModel().blockSignals(True)
            self.data_widget.cameraTree.selectionModel().clearSelection()
            self.data_widget.cameraTree.selectionModel().blockSignals(False)

        if len(item_selection.indexes()) == 0:
            return ()

        self.selected_index = self.find_selected_tree_index(item_selection)
        self.set_survey_id_and_list_from_selected_index()

        self.setup_processing_button_names()
        self.enable_tabs()
        if self.survey_id is None:
            # logger.info(selected_index.data(Qt.DisplayRole))
            # logger.info("columns " + str(selected_index.model().columnCount()))
            # logger.info("rows " + str(selected_index.model().rowCount()))
            # logger.info("children: " + str(len(selected_index.model().children())))

            descendant_surveys = self.get_all_descendants(self.selected_index)
            survey_stats = SurveyStats()
            survey_stats.calculate_surveys(descendant_surveys)
            self.survey_stats_to_ui(survey_stats)
            self.non_survey_to_stats_ui(self.selected_index.data(Qt.DisplayRole))

            logger.info(descendant_surveys)

        else:

            self.data_to_ui()
            self.display_cots_detections(samba=False)
            self.load_thumbnails()
            self.load_marks()
            self.load_inference_charts()

        self.tab_changed(self.read_current_tab())

        self.set_hint()

    # if a single sequence is selected the processing tabs (enhance, inference and EOD) should
    # process only that sequence
    # If a folder is selected it should process all of the sequences in that folder
    # This method changes the words on the buttons to reflect that
    # Also some features are disabled
    def setup_processing_button_names(self):
        folder_name = self.selected_index.data()
        if self.survey_id is None:
            self.enhance_widget.btnEnhanceOpenFolder.setVisible(False)
            self.inference_widget.btnInferenceOpenFolder.setVisible(False)
            if folder_name == "Local Drive":
                self.enhance_widget.btnEnhanceFolder.setText(f"Enhance all photos")
                self.inference_widget.btnInferenceFolder.setText(f"Inference all photos")
                self.eod_cots_widget.detectCotsButton.setText(f"Detect COTS in all photos")
            else:
                self.enhance_widget.btnEnhanceFolder.setText(f"Enhance all photos for {folder_name}")
                self.inference_widget.btnInferenceFolder.setText(f"Inference all photos for {folder_name}")
                self.eod_cots_widget.detectCotsButton.setText(f"Detect COTS in all photos for {folder_name}")
        else:
            self.enhance_widget.btnEnhanceOpenFolder.setVisible(os.path.exists(self.enhanced_folder(self.survey().folder)))
            self.inference_widget.btnInferenceOpenFolder.setVisible(True)
            self.enhance_widget.btnEnhanceFolder.setText(f"Enhance Photos for sequence {folder_name}")
            self.inference_widget.btnInferenceFolder.setText(f"Inference photos for {folder_name}")
            self.eod_cots_widget.detectCotsButton.setText(f"Detect COTS in photos for {folder_name}")

    def find_selected_tree_index(self, item_selection):
        for index in item_selection.indexes():
            selected_index = index
        return selected_index

    def check_save(self):
        if self.is_modified():
            msgBox = QMessageBox()
            msgBox.setText(self.tr("Do you want to save your changes?"))
            msgBox.setWindowTitle(self.tr('Save?'))
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            msgBox.button(QMessageBox.Yes).setText(self.tr("Yes"))
            msgBox.button(QMessageBox.No).setText(self.tr("No"))

            reply = msgBox.exec()

            if reply == QMessageBox.Yes:
                self.ui_to_data()
            else:
                self.data_to_ui()

    def get_all_descendants_as_surveys(self, selected_index):
        survey_infos = self.get_all_descendants(selected_index)
        surveys = []
        for survey_info in survey_infos:
            survey = state.model.surveys_data[survey_info["survey_id"]]
            surveys.append(survey)
        return surveys

    def get_all_descendants(self, selected_index):
        if selected_index.data(Qt.UserRole) is not None:
            return [selected_index.data(Qt.UserRole)]

        ret = []
        row = 0
        child = selected_index.child(row, 0)
        while child.data(Qt.DisplayRole) is not None:
            ret.extend(self.get_all_descendants(child))
            # logger.info(child.data(Qt.DisplayRole))
            row += 1
            child = selected_index.child(row, 0)
        return ret

    def xstr(self, s):
        if s is None:
            return ''
        return str(s)

    def survey(self) -> Survey:
        if self.survey_list is None:
            return None
        else:
            return self.survey_list.get(self.survey_id)

    def is_modified(self):
        if self.survey_id is None:
            return False
        return self.xstr(self.survey().site) != self.metadata_widget.ed_site.text() or \
               self.xstr(self.survey().operator) != self.metadata_widget.ed_operator.text() or \
               self.xstr(self.survey().observer) != self.metadata_widget.ed_observer.text() or \
               self.xstr(self.survey().vessel) != self.metadata_widget.ed_vessel.text() or \
               self.xstr(self.survey().sea) != self.metadata_widget.cb_sea.currentData() or \
               self.xstr(self.survey().wind) != self.metadata_widget.cb_wind.currentText() or \
               self.xstr(self.survey().cloud) != self.metadata_widget.cb_cloud.currentText() or \
               self.xstr(self.survey().visibility) != self.metadata_widget.cb_vis.currentText() or \
               self.xstr(self.survey().comments) != self.metadata_widget.ed_comments.toPlainText() or \
               self.xstr(self.survey().tide) != self.metadata_widget.cb_tide.currentData() or \
               self.xstr(self.survey().friendly_name) != self.metadata_widget.ed_name.text() or \
               ( not self.metadata_widget.cb_reefcloud_project.currentText().endswith("Permission Denied") and
                 (self.xstr(self.survey().reefcloud_project) != self.metadata_widget.cb_reefcloud_project.currentText() or
                  self.survey().reefcloud_site != self.metadata_widget.cb_reefcloud_site.currentData())
                 )

    def ui_to_data(self):
        if self.thumbnail_model is not None:
            self.thumbnail_model.interrupt()

        if self.survey_id is not None:
            self.survey().site = self.metadata_widget.ed_site.text()
            self.survey().operator = self.metadata_widget.ed_operator.text()
            self.survey().observer = self.metadata_widget.ed_observer.text()
            self.survey().vessel = self.metadata_widget.ed_vessel.text()
            self.survey().sea = self.metadata_widget.cb_sea.currentData()
            self.survey().wind = self.metadata_widget.cb_wind.currentText()
            self.survey().cloud = self.metadata_widget.cb_cloud.currentText()
            self.survey().visibility = self.metadata_widget.cb_vis.currentText()
            self.survey().comments = self.metadata_widget.ed_comments.toPlainText()
            self.survey().tide = self.metadata_widget.cb_tide.currentData()
            self.survey().friendly_name = self.metadata_widget.ed_name.text()
            if not self.metadata_widget.cb_reefcloud_project.currentText().endswith("Permission Denied"):
                self.survey().reefcloud_project = self.metadata_widget.cb_reefcloud_project.currentText()
                self.survey().reefcloud_site = self.metadata_widget.cb_reefcloud_site.currentData()

            if not state.read_only:
                backup_folder = state.backup_folder
                if self.camera_tree_selected:
                    backup_folder = None
                save_survey(self.survey(), state.primary_folder, backup_folder, False)

    def data_to_ui(self):
        if self.survey_id is not None:
            self.metadata_widget.ed_site.setText(self.xstr(self.survey().site))
            self.metadata_widget.ed_name.setText(self.xstr(self.survey().friendly_name))
            self.metadata_widget.ed_operator.setText(self.xstr(self.survey().operator))
            self.metadata_widget.ed_observer.setText(self.xstr(self.survey().observer))
            self.metadata_widget.ed_vessel.setText(self.xstr(self.survey().vessel))
            self.metadata_widget.cb_sea.setCurrentText(self.xstr(self.survey().sea))
            self.metadata_widget.cb_wind.setCurrentText(self.xstr(self.survey().wind))
            self.metadata_widget.cb_cloud.setCurrentText(self.xstr(self.survey().cloud))
            self.metadata_widget.cb_vis.setCurrentText(self.xstr(self.survey().visibility))
            self.metadata_widget.cb_tide.setCurrentText(self.xstr(self.survey().tide))

            if (self.metadata_widget.cb_reefcloud_project.findText(self.survey().reefcloud_project) == -1):
                project_name = f"{self.survey().reefcloud_project} - Permission Denied"
                if  (self.metadata_widget.cb_reefcloud_project.findText(project_name) == -1):
                    self.metadata_widget.cb_reefcloud_project.addItem(project_name)
                self.metadata_widget.cb_reefcloud_project.setCurrentText(project_name)
            else:
                self.metadata_widget.cb_reefcloud_project.setCurrentText(self.survey().reefcloud_project)
            self.cb_reefcloud_project_changed(None)

            site_id = self.survey().reefcloud_site
            try:
                site_name = self.site_lookup[site_id]
            except:
                site_name = ""
            self.metadata_widget.cb_reefcloud_site.setCurrentText(site_name)

            self.metadata_widget.ed_comments.setPlainText(self.survey().comments)

            self.info_widget.lb_sequence_name.setText(self.survey().id)
            self.info_widget.lb_start_time.setText(utc_to_local(self.survey().start_date, timezone=self.time_zone))
            self.info_widget.lb_end_time.setText(utc_to_local(self.survey().finish_date, timezone=self.time_zone))
            self.info_widget.lb_start_waypoint.setText(
                self.start_waypoint_as_text())
            self.info_widget.lb_end_waypoint.setText(
                self.finish_waypoint_as_text())
            self.data_widget.folder_label.setText(self.survey().folder)
            survey_stats = SurveyStats()
            survey_stats.calculate(self.survey())
            self.survey_stats_to_ui(survey_stats)

            self.disable_save_cancel()

    def start_waypoint_as_text(self):
        lon = self.survey().start_lon
        if lon is None:
            lon = ""
        lat = self.survey().start_lat
        if lat is None:
            lat = ""
        depth = self.survey().start_depth if self.survey().start_depth else None
        if depth is None:
            depth = ""
        else:
            depth = round(depth)
        return f"{lon} {lat} {depth}m"

    def finish_waypoint_as_text(self):
        lon = self.survey().finish_lon
        if lon is None:
            lon = ""
        lat = self.survey().finish_lat
        if lat is None:
            lat = ""
        depth = self.survey().finish_depth if self.survey().finish_depth else None
        if depth is None:
            depth = ""
        else:
            depth = round(depth)
        return f"{lon} {lat} {depth}m"

    def survey_stats_to_ui(self, survey_stats):
        self.info_widget.lb_number_images.setText(str(survey_stats.photos))
        self.info_widget.lbl_missing_gps.setText(str(survey_stats.missing_gps))
        self.info_widget.lbl_missing_ping.setText(str(survey_stats.missing_ping_depth))
        self.info_widget.lbl_missing_pressure.setText(str(survey_stats.missing_pressure_depth))
        self.info_widget.distance_label.setText(f"{survey_stats.min_ping} to {survey_stats.max_ping} metres")

    def load_thumbnails(self):
        from aims.gui_model.lazy_list_model import LazyListModel

        if self.thumbnail_model is not None:
            self.thumbnail_model.interrupt()
        list_thumbnails: QListView = self.data_widget.lv_thumbnails
        list_thumbnails.setViewMode(QListWidget.IconMode)
        list_thumbnails.setIconSize(QSize(200, 200))
        list_thumbnails.setResizeMode(QListWidget.Adjust)
        if self.survey_id is not None:
            folder = self.survey().folder
            samba = self.survey().samba
            file_ops = get_file_ops(samba)
            photos = [name for name in file_ops.listdir(folder) if
                      name.lower().endswith(".jpg") or name.lower().endswith(".jpeg")]
            photos.sort()
            self.thumbnail_model = LazyListModel(photos, folder, self.survey_id, samba)
            list_thumbnails.setModel(self.thumbnail_model)
            list_thumbnails.clicked.connect(self.thumbnail_clicked)

    def thumbnail_clicked(self, index):
        self.data_widget.file_info_label.setText(self.file_info(self.thumbnail_model.data(index, Qt.UserRole)))

    def file_info(self, filename):
        exif = get_exif_data(filename, False)
        short_filename = os.path.basename(filename)
        return f"{short_filename} total_depth: {exif['altitude']} subject_distance: {exif['subject_distance']}"

    def load_explore_surveys_tree(self):
        self.check_save()

        state.config.camera_connected = False
        data_loader.load_data_model(aims_status_dialog=self.aims_status_dialog)
        tree = self.data_widget.surveysTree
        self.surveys_tree_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_camera=False,
                                                                   checkable=False)
        tree.setModel(self.surveys_tree_model)
        tree.expandRecursively(self.surveys_tree_model.invisibleRootItem().index(), 3)
        self.data_widget.surveysTree.selectionModel().selectionChanged.connect(self.explore_tree_selection_changed)
        self.survey_id = None

    def map_load_finished(self, success):
        logger.info(f"Map loaded success:{success}")

    def non_survey_to_stats_ui(self, name):
        self.info_widget.lb_sequence_name.setText(name)
        self.info_widget.lb_start_time.setText("")
        self.info_widget.lb_end_time.setText("")
        self.info_widget.lb_start_waypoint.setText("")
        self.info_widget.lb_end_waypoint.setText("")

    def set_hint(self):
        ready_to_edit = self.survey_id is not None
        ready_to_download = len(checked_survey_ids(self.camera_model)) > 0
        if ready_to_edit and ready_to_download:
            self.hint_function(self.tr("Edit the metadata or Click the download button"))

        if ready_to_edit and not ready_to_download:
            self.hint_function(self.tr("Edit the metadata"))

        if not ready_to_edit and ready_to_download:
            self.hint_function(self.tr("Click the download button"))

        if not ready_to_edit and not ready_to_download:
            if state.model.camera_data_loaded:
                self.hint_function(
                    self.tr("Click on a survey name to edit metadata or check the surveys that you want to download"))
            else:
                self.hint_function(self.tr("Click on a survey name to edit metadata"))

