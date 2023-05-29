import datetime
import logging
import os
import shutil
import subprocess
import time
from time import process_time
from fabric import Connection

from PyQt5 import QtCore, uic, QtGui, QtWidgets, QtTest
from PyQt5.QtCore import QModelIndex, QItemSelection, QSize, Qt, QTimer
from PyQt5.QtGui import QPixmap, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QInputDialog, QWidget, QTableView, QLabel, QListView, \
    QListWidget, QMessageBox, QMainWindow
from pytz import utc
from reefscanner.basic_model.model_helper import rename_folders
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims import state
from aims.gui_model.lazy_list_model import LazyListModel
from aims.gui_model.marks_model import MarksModel
from aims.gui_model.tree_model import TreeModelMaker, checked_survey_ids
from aims.operations.kml_maker import make_kml
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.stats.survey_stats import SurveyStats
from aims.ui.main_ui_components.utils import setup_folder_tree, setup_file_system_tree_and_combo_box, clearLayout, \
    update_data_folder_from_tree
from aims.ui.map_html import map_html_str

from aims.operations.enhance_photo_operation import EnhancePhotoOperation

logger = logging.getLogger("")


def utc_to_local(utc_str, timezone):
    try:
        naive_date = datetime.datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S")
        utc_date = utc.localize(naive_date)
        local_date = utc_date.astimezone(timezone)
        return datetime.datetime.strftime(local_date, "%Y-%m-%d %H:%M:%S")
    except:
        return utc_str


class DataComponent(QMainWindow):
    def __init__(self, hint_function):
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

    def tab_changed(self, index):
        print(index)
        if index == 2:
            self.draw_map()

    def load_data_screen(self, fixed_drives, aims_status_dialog, time_zone):

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

        self.info_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_info.ui',
                                                    self.data_widget.info_tab)
        self.metadata_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_metadata.ui',
                                                        self.data_widget.metadata_tab)
        self.marks_widget = self.load_sequence_frame(f'{state.meipass}resources/marks.ui',
                                                     self.data_widget.marks_tab)
        self.enhance_widget = self.load_sequence_frame(f'{state.meipass}resources/enhance.ui',
                                                     self.data_widget.enhance_tab)
        
        self.lookups()
        self.data_widget.tabWidget.currentChanged.connect(self.tab_changed)
        self.data_widget.renameFoldersButton.clicked.connect(self.rename_folders)
        self.data_widget.refreshButton.clicked.connect(self.refresh)
        self.data_widget.kmlForAllButton.clicked.connect(self.kml_for_all)
        self.data_widget.kmlForOneButton.clicked.connect(self.kml_for_one)

        self.marks_widget.btnOpenMarkFolder.clicked.connect(self.open_mark_folder)
        self.marks_widget.btnOpenMark.clicked.connect(self.open_mark)
        self.data_widget.open_folder_button.clicked.connect(self.open_folder)
        self.data_widget.tabWidget.setCurrentIndex(0)
        self.data_widget.tabWidget.setEnabled(False)
        self.survey_id = None
        self.metadata_widget.cancelButton.clicked.connect(self.data_to_ui)
        self.metadata_widget.saveButton.clicked.connect(self.ui_to_data)

        self.load_explore_surveys_tree()


        self.data_widget.downloadButton.clicked.connect(self.download)
        self.data_widget.showDownloadedCheckBox.stateChanged.connect(self.show_downloaded_changed)
        self.data_widget.deleteDownloadedButton.clicked.connect(self.delete_downloaded)

        if self.setup_camera_tree():
            self.data_widget.camera_not_connected_label.setVisible(False)
            self.data_widget.camera_panel.setVisible(True)
        else:
            self.data_widget.camera_not_connected_label.setVisible(True)
            self.data_widget.camera_panel.setVisible(False)

        self.initial_disables()
        self.set_hint()
        self.data_widget.mapView.loadFinished.connect(self.map_load_finished)

        self.enhance_widget.btnEnhanceOpenFolder.clicked.connect(self.enhance_open_folder)
        self.enhance_widget.btnEnhanceFolder.clicked.connect(self.enhance_photos_folder)
        self.enhance_widget.textEditSuffix.setPlainText("")
        self.enhance_widget.textEditOutputFolder.setPlainText("enhanced")
        self.enhance_widget.textEditCPULoad.setPlainText("0.01")
        self.enhance_widget.checkBoxOutputFolder.setChecked(False)
        self.enhance_widget.checkBoxSuffix.setChecked(False)
        self.enhance_widget.textEditOutputFolder.setEnabled(False)
        self.enhance_widget.textEditSuffix.setEnabled(False)

        self.enhance_widget.checkBoxOutputFolder.stateChanged.connect(self.enhance_widget_cb_outputfolder_changed)
        self.enhance_widget.checkBoxSuffix.stateChanged.connect(self.enhance_widget_cb_suffix_changed)


    def enhance_widget_cb_suffix_changed(self, state):
        self.enhance_widget.textEditSuffix.setEnabled(state != 0)

    def enhance_widget_cb_outputfolder_changed(self, state):
        self.enhance_widget.textEditOutputFolder.setEnabled(state != 0)

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
        reply = QMessageBox.question(self.data_widget, self.tr('Delete?'), self.tr("Are you sure you want to delete the downloaded surveys from the camera?"),
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            archive_folder = "/media/jetson/*/images/archive"
            conn = Connection(
                "jetson@" + state.config.camera_ip,
                connect_kwargs={"password": "jetson"}
            )
            conn.run("rm -r " + archive_folder, hide=True)

        state.model.archived_data_loaded = False
        self.setup_camera_tree()

    def download(self):
        self.check_save()
        self.survey_id = None
        self.data_widget.surveysTree.selectionModel().clearSelection()
        self.data_widget.cameraTree.selectionModel().clearSelection()

        start = process_time()
        surveys = checked_survey_ids(self.camera_model)

        self.check_space(surveys)

        if len(surveys) == 0:
            raise Exception("Please select at least one survey")

        operation = SyncFromHardwareOperation(state.config.hardware_data_folder, state.primary_folder, state.backup_folder, surveys, state.config.camera_samba)
        operation.update_interval = 1
        self.aims_status_dialog.set_operation_connections(operation)
        # # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.close()

        state.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)

        state.model.archived_data_loaded = False
        self.setup_camera_tree()
        self.load_explore_surveys_tree()

        end = process_time()
        minutes = (end-start)/60

        print(f"Download Finished in {minutes} minutes")
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText(self.tr("Download finished"))
        errorbox.setDetailedText(self.tr("Finished in ") + str(minutes) + self.tr(" minutes"))
        self.aims_status_dialog.progress_dialog.close()
        QtTest.QTest.qWait(1000)
        errorbox.exec_()
        self.initial_disables()

    def setup_camera_tree(self):
        if state.model.camera_data_loaded:
            show_downloaded = self.data_widget.showDownloadedCheckBox.isChecked()
            state.load_archive_data_model(aims_status_dialog=self.aims_status_dialog)
            camera_tree = self.data_widget.cameraTree
            self.camera_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_local=False, include_archives=show_downloaded, checkable=True)
            camera_tree.setModel(self.camera_model)
            self.camera_model.itemChanged.connect(self.camera_on_itemChanged)
            self.data_widget.cameraTree.selectionModel().selectionChanged.connect(self.camera_tree_selection_changed)
            camera_tree.expandRecursively(self.camera_model.invisibleRootItem().index(), 3)
            return True
        else:
            return False

    def camera_on_itemChanged(self, item):
        print ("Item change")
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
        for project in state.config.reefcloud_projects:
            self.metadata_widget.cb_reefcloud_project.addItem(project)

        self.metadata_widget.cb_reefcloud_site.addItem("", userData="")

        self.metadata_widget.cb_reefcloud_project.currentIndexChanged.connect(self.cb_reefcloud_project_changed)


    def cb_reefcloud_project_changed(self, index):
        # figure out what project was selected.
        project = self.metadata_widget.cb_reefcloud_project.currentText()
        if project == "":
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
        self.check_save()
        old_survey_id = self.survey_id
        self.ui_to_data()
        self.survey_id = None
        try:
            rename_folders(state.model, self.time_zone)
        except:
            raise Exception("Error renaming folders. Maybe you have a file or folder open in another window.")

        self.load_explore_surveys_tree()
        self.setup_camera_tree()
        self.survey_id = old_survey_id
        self.data_to_ui()

        print("rename done")

    def kml_for_all(self):
        for survey in state.model.surveys_data.values():
            make_kml(survey)

    def kml_for_one(self):
        if self.survey() is None:
            raise Exception ("Choose a survey first")
        make_kml(survey=self.survey())

    def refresh(self):
        self.check_save()
        old_survey_id = self.survey_id
        self.ui_to_data()
        self.survey_id = None
        self.load_explore_surveys_tree()
        self.setup_camera_tree()
        self.survey_id = old_survey_id
        self.data_to_ui()
        print("refresh done")

    def load_sequence_frame(self, ui_file, parent_widget):
        clearLayout(parent_widget.layout())
        widget: QWidget = uic.loadUi(ui_file)
        parent_widget.layout().addWidget(widget)
        return widget

    def load_marks(self):
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
        os.startfile(self.survey().folder)

    def open_mark(self):
        if self.mark_filename is not None:
            os.startfile(self.mark_filename)

    def open_mark_folder(self):
        if self.mark_filename is not None:
            try:
                fname = self.mark_filename.replace("//", "/")
                fname = fname.replace("/", "\\")
                command = f'explorer.exe /select,"{fname}"'
                print(command)
                subprocess.call(command)
            except:
                os.startfile(self.mark_filename, "open")

    def enhance_open_folder(self):
        os.startfile(self.survey().folder)

    def enhance_photos_folder(self):
        output_suffix = self.enhance_widget.textEditSuffix.toPlainText()
        cpu_load_string = self.enhance_widget.textEditCPULoad.toPlainText()


        output_folder = self.enhance_widget.textEditOutputFolder.toPlainText() if self.enhance_widget.checkBoxOutputFolder.isChecked() else 'enhanced'
        output_suffix = self.enhance_widget.textEditSuffix.toPlainText() if self.enhance_widget.checkBoxSuffix.isChecked() else None

        self.enhance_widget.textBrowser.append("Photoenhance starting")
        self.enhance_widget.textBrowser.append(f"Enhanced photos will be saved in the folder \'{output_folder}\'") 
        if self.enhance_widget.checkBoxSuffix.isChecked():
            self.enhance_widget.textBrowser.append(f"Enhanced photos will be saved with the suffix \'_{output_suffix}\'") 

        QApplication.processEvents()
        # photoenhance(target=self.survey().folder, load=float(cpu_load_string), suffix=output_suffix, stronger_contrast_deep=str(stronger_enhancement), disable_denoising=str(disable_denoising))

        enhance_operation = EnhancePhotoOperation(target=self.survey().folder, load=float(cpu_load_string), suffix=output_suffix, output_folder=output_folder)
        enhance_operation.update_interval = 1
        self.aims_status_dialog.set_operation_connections(enhance_operation)
        # # operation.after_run.connect(self.after_sync)
        logger.info("done connections")
        result = self.aims_status_dialog.threadPool.apply_async(enhance_operation.run)
        logger.info("thread started")
        while not result.ready():
            QApplication.processEvents()
        logger.info("thread finished")
        self.aims_status_dialog.close()

        self.enhance_widget.textBrowser.append("Photoenhance done")


    def camera_tree_selection_changed(self, item_selection: QItemSelection):
        print("camera tree changed")
        self.check_save()
        self.data_widget.surveysTree.selectionModel().clearSelection()
        if len(item_selection.indexes()) == 0:
            return ()

        selected_index = self.find_selected_tree_index(item_selection)
        self.set_survey_id_and_list_from_selected_index(selected_index)

        print(f"survey_id {self.survey_id}")
        print(f"survey {self.survey()}")

        if self.survey_id is None:
            self.disable_all_tabs(0)
        else:
            self.enable_metadata_tab_only()

        self.data_to_ui()
        self.set_hint()


    def set_survey_id_and_list_from_selected_index(self, selected_index):
        selected_index_data = selected_index.data(Qt.UserRole)
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

    def enable_metadata_tab_only(self):
        self.data_widget.tabWidget.setEnabled(True)
        self.data_widget.tabWidget.setTabEnabled(0, False)
        self.data_widget.tabWidget.setTabEnabled(1, False)
        self.data_widget.tabWidget.setTabEnabled(2, True)
        self.data_widget.tabWidget.setTabEnabled(3, False)
        self.data_widget.tabWidget.setTabEnabled(4, False)
        self.data_widget.tabWidget.setTabEnabled(5, False)
        self.data_widget.tabWidget.setCurrentIndex(2)

    def disable_all_tabs(self, index):
        self.data_widget.tabWidget.setEnabled(False)
        self.data_widget.tabWidget.setCurrentIndex(index)


    def enable_all_tabs(self):
        self.data_widget.tabWidget.setEnabled(True)
        self.data_widget.tabWidget.setTabEnabled(0, False)
        self.data_widget.tabWidget.setTabEnabled(1, True)
        self.data_widget.tabWidget.setTabEnabled(2, True)
        self.data_widget.tabWidget.setTabEnabled(3, True)
        self.data_widget.tabWidget.setTabEnabled(4, True)
        self.data_widget.tabWidget.setTabEnabled(5, True)
        # self.data_widget.tabWidget.setCurrentIndex(2)


    def explore_tree_selection_changed(self, item_selection: QItemSelection):
        self.check_save()
        if self.data_widget.cameraTree.selectionModel() is not None:
            self.data_widget.cameraTree.selectionModel().clearSelection()

        if len(item_selection.indexes()) == 0:
            return ()

        selected_index = self.find_selected_tree_index(item_selection)
        self.set_survey_id_and_list_from_selected_index(selected_index)

        if self.survey_id is None:
            self.disable_all_tabs(1)
            print(selected_index.data(Qt.DisplayRole))
            print("columns " + str(selected_index.model().columnCount()))
            print("rows " + str(selected_index.model().rowCount()))
            print("children: " + str(len(selected_index.model().children())))

            descendant_surveys = self.get_all_descendants(selected_index)
            survey_stats = SurveyStats()
            survey_stats.calculate_surveys(descendant_surveys)
            self.survey_stats_to_ui(survey_stats)
            self.non_survey_to_stats_ui(selected_index.data(Qt.DisplayRole))

            print(descendant_surveys)

        else:
            self.enable_all_tabs()

            self.data_to_ui()
            self.draw_map()
            self.load_thumbnails()
            self.load_marks()

        self.set_hint()

    def find_selected_tree_index(self, item_selection):
        for index in item_selection.indexes():
            selected_index = index
        return selected_index

    def check_save(self):
        if self.is_modified():
            reply = QMessageBox.question(self.data_widget, self.tr('Save?'), self.tr("Do you want to save your changes?"),
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.ui_to_data()

    def get_all_descendants(self, selected_index):
        if selected_index.data(Qt.UserRole) is not None:
            return [selected_index.data(Qt.UserRole)]

        ret = []
        row = 0
        child = selected_index.child(row, 0)
        while child.data(Qt.DisplayRole) is not None:
            ret.extend(self.get_all_descendants(child))
            print(child.data(Qt.DisplayRole))
            row += 1
            child = selected_index.child(row, 0)
        return ret

    def xstr(self, s):
        if s is None:
            return ''
        return str(s)

    def survey(self):
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
               self.xstr(self.survey().reefcloud_project) != self.metadata_widget.cb_reefcloud_project.currentText() or \
               self.survey().reefcloud_site != self.metadata_widget.cb_reefcloud_site.currentData()

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
            self.survey().reefcloud_project = self.metadata_widget.cb_reefcloud_project.currentText()
            self.survey().reefcloud_site = self.metadata_widget.cb_reefcloud_site.currentData()

            save_survey(self.survey(), state.primary_folder, state.backup_folder, False)

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
            self.info_widget.lb_start_waypoint.setText(f"{self.survey().start_lon} {self.survey().start_lat}")
            self.info_widget.lb_end_waypoint.setText(f"{self.survey().finish_lon} {self.survey().finish_lat}")
            self.data_widget.folder_label.setText(self.survey().folder)
            survey_stats = SurveyStats()
            survey_stats.calculate(self.survey())
            self.survey_stats_to_ui(survey_stats)

            self.disable_save_cancel()

    def survey_stats_to_ui(self, survey_stats):
        self.info_widget.lb_number_images.setText(str(survey_stats.photos))
        self.info_widget.lbl_missing_gps.setText(str(survey_stats.missing_gps))
        self.info_widget.lbl_missing_ping.setText(str(survey_stats.missing_ping_depth))
        self.info_widget.lbl_missing_pressure.setText(str(survey_stats.missing_pressure_depth))

    def load_thumbnails(self):
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
            self.thumbnail_model = LazyListModel(photos, folder, self.survey_id, samba)
            list_thumbnails.setModel(self.thumbnail_model)

    def load_explore_surveys_tree(self):
        self.ui_to_data()

        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)
        tree = self.data_widget.surveysTree
        self.surveys_tree_model = TreeModelMaker().make_tree_model(timezone=self.time_zone, include_camera=False, checkable=False)
        tree.setModel(self.surveys_tree_model)
        tree.expandRecursively(self.surveys_tree_model.invisibleRootItem().index(), 3)
        self.data_widget.surveysTree.selectionModel().selectionChanged.connect(self.explore_tree_selection_changed)
        self.survey_id = None

    def draw_map(self):
        print("draw map")
        if self.survey_id is not None:
            folder = self.survey().folder
            html_str = map_html_str(folder, False)
            print(html_str)
            if html_str is not None:
                view: QWebEngineView = self.data_widget.mapView
                # view.stop()
                view.setHtml(html_str)

        print("finished draw map")

    def map_load_finished(self, success):
        print (f"Map loaded success:{success}")

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
                self.hint_function(self.tr("Click on a survey name to edit metadata or check the surveys that you want to download"))
            else:
                self.hint_function(self.tr("Click on a survey name to edit metadata"))


    def check_space(self, surveys):
        try:
            total_kilo_bytes_used = 0
            for survey in surveys:
                if survey['branch'] == self.tr("New Sequences"):
                    command = f'du -s /media/jetson/*/images/{survey["survey_id"]}'
                else:
                    command = f'du -s /media/jetson/*/images/archive/{survey["survey_id"]}'

                conn = Connection(
                    "jetson@" + state.config.camera_ip,
                    connect_kwargs={"password": "jetson"}
                )
                result = conn.run(command, hide=True)
                kilo_bytes_used = int(result.stdout.split()[0])
                print(self.tr("Bytes used: ") + f"{kilo_bytes_used}")
                total_kilo_bytes_used += kilo_bytes_used

            print(self.tr("total Bytes used: ") + f"{total_kilo_bytes_used}")

            print(state.primary_drive)
            print(state.backup_drive)

            du = shutil.disk_usage(state.primary_drive)
        except Exception as e:
            logger.error(self, "Error calulating disk usage or space. ", exc_info=True)
            return

        not_enough_disk = self.tr("Not enough disk space available on the primary disk.")
        not_enough_disk_back = self.tr("Not enough disk space available on the backup disk.")
        required = self.tr("Selected sequences require")
        avaliable = self.tr("Space available on")
        _is_ = self.tr("is")

        if total_kilo_bytes_used > du.free * 1000:
            gb_used = total_kilo_bytes_used / 1000000
            free_gb = du.free / 1000000000

            message = f"""
                {not_enough_disk}\n
                {required} {gb_used:.2f Gb}
                {avaliable} {state.primary_drive} {_is_} {free_gb:.2f} Gb
                """
            raise Exception(message)

        if state.backup_drive is not None:
            if total_kilo_bytes_used > du.free * 1000:
                du = shutil.disk_usage(state.backup_drive)
                gb_used = total_kilo_bytes_used / 1000000
                free_gb = du.free / 1000000000
                message = f"""
                    {not_enough_disk_back}\n
                    {required} {gb_used:.2f Gb}
                    {avaliable} {state.primary_drive} {_is_} {free_gb:.2f} Gb
                    """
                raise Exception(message)




