import datetime
import logging
import os
import subprocess

from PyQt5 import QtCore, uic, QtGui
from PyQt5.QtCore import QModelIndex, QItemSelection, QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QInputDialog, QWidget, QTableView, QLabel, QListView, \
    QListWidget, QMessageBox
from pytz import utc
from reefscanner.basic_model.reader_writer import save_survey
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims import state
from aims.gui_model.lazy_list_model import LazyListModel
from aims.gui_model.marks_model import MarksModel
from aims.gui_model.tree_model import make_tree_model
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.stats.survey_stats import SurveyStats
from aims.ui.main_ui_components.utils import setup_folder_tree, setup_file_system_tree_and_combo_box, clearLayout, \
    update_data_folder_from_tree
from aims.ui.map_html import map_html_str


logger = logging.getLogger(__name__)

def utc_to_local(utc_str, timezone):
    try:
        naive_date = datetime.datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S")
        utc_date = utc.localize(naive_date)
        local_date = utc_date.astimezone(timezone)
        return datetime.datetime.strftime(local_date, "%Y-%m-%d %H:%M:%S")
    except:
        return utc_str


class ExploreComponent:
    def __init__(self):
        self.explore_widget = None
        self.metadata_widget = None
        self.info_widget = None
        self.marks_widget = None

        self.camera_model = None
        self.survey_id = None
        self.thumbnail_model = None

        self.marks_table: None
        self.mark_filename = None
        self.marks_model = None
        self.aims_status_dialog = None

        self.time_zone = None


    def tab_changed(self, index):
        print(index)
        if index == 3:
            self.draw_map()

    def load_explore_screen(self, fixed_drives, aims_status_dialog, time_zone):

        self.time_zone = time_zone

        self.aims_status_dialog = aims_status_dialog

        self.info_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_info.ui', self.explore_widget.info_tab)
        self.metadata_widget = self.load_sequence_frame(f'{state.meipass}resources/sequence_metadata.ui', self.explore_widget.metadata_tab)
        self.marks_widget = self.load_sequence_frame(f'{state.meipass}resources/marks.ui', self.explore_widget.marks_tab)

        self.lookups()
        self.explore_widget.tabWidget.currentChanged.connect(self.tab_changed)

        self.marks_widget.btnOpenMarkFolder.clicked.connect(self.open_mark_folder)
        self.marks_widget.btnOpenMark.clicked.connect(self.open_mark)
        self.explore_widget.open_folder_button.clicked.connect(self.open_folder)
        self.explore_widget.tabWidget.setCurrentIndex(0)
        self.explore_widget.tabWidget.setEnabled(False)
        self.survey_id = None
        self.metadata_widget.cancelButton.clicked.connect(self.data_to_ui)
        self.metadata_widget.saveButton.clicked.connect(self.ui_to_data)

        self.load_explore_surveys_tree(self.aims_status_dialog)

    def lookups(self):

        self.metadata_widget.cb_tide.addItem("")
        self.metadata_widget.cb_tide.addItem("Falling")
        self.metadata_widget.cb_tide.addItem("High")
        self.metadata_widget.cb_tide.addItem("Low")
        self.metadata_widget.cb_tide.addItem("Rising")

        self.metadata_widget.cb_sea.addItem("")
        self.metadata_widget.cb_sea.addItem("calm")
        self.metadata_widget.cb_sea.addItem("slight")
        self.metadata_widget.cb_sea.addItem("moderate")
        self.metadata_widget.cb_sea.addItem("rough")

        self.metadata_widget.cb_wind.addItem("")
        self.metadata_widget.cb_wind.addItem("<5")
        self.metadata_widget.cb_wind.addItem("5-10")
        self.metadata_widget.cb_wind.addItem("10-15")
        self.metadata_widget.cb_wind.addItem("15-20")
        self.metadata_widget.cb_wind.addItem("20-25")
        self.metadata_widget.cb_wind.addItem("25-30")
        self.metadata_widget.cb_wind.addItem(">30")

        self.metadata_widget.cb_cloud.addItem("")
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



    def load_sequence_frame(self, ui_file, parent_widget):
        clearLayout(parent_widget.layout())
        widget: QWidget = uic.loadUi(ui_file)
        parent_widget.layout().addWidget(widget)
        return widget

    def load_marks(self):
        self.marks_table: QTableView = self.marks_widget.tableView
        self.mark_filename = None
        self.marks_model = MarksModel(self.survey_col("json_folder"))
        self.marks_table.setModel(self.marks_model)
        self.marks_table.selectionModel().currentChanged.connect(self.marks_table_clicked)
        if self.marks_model.hasData():
            self.marks_table.selectRow(0)
        else:
            label: QLabel = self.marks_widget.lblPhoto
            label.clear()
            self.marks_widget.lblFileName.setText("There are no marks for this survey")

    def marks_table_clicked(self, selected, deselected):
        index = selected
        if self.marks_model is not None:
            self.mark_filename = self.marks_model.photo_file(index.row())
            self.marks_widget.lblFileName.setText(self.marks_model.photo_file_name(index.row()))
            label:QLabel = self.marks_widget.lblPhoto
            pixmap = QPixmap(self.mark_filename).scaled(label.size().width(), label.size().height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)

    def open_folder(self):
        os.startfile(self.survey_col("json_folder"))

    def open_mark(self):
        if self.mark_filename is not None:
            os.startfile(self.mark_filename)

    def open_mark_folder(self):
        if self.mark_filename is not None:
            try:
                fname = self.mark_filename.replace("//", "/")
                fname = fname.replace("/", "\\")
                command = f'explorer.exe /select,"{fname}"'
                print (command)
                subprocess.call(command)
            except:
                os.startfile(self.mark_filename, "open")

    def explore_tree_selection_changed(self,  item_selection:QItemSelection):
        if self.is_modified():
            reply = QMessageBox.question(self.explore_widget, 'Save?', "Do you want to save your changes?", QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.ui_to_data()

        if len(item_selection.indexes()) == 0:
            return()

        for index in item_selection.indexes():
            self.survey_id = index.data(Qt.UserRole)
            selected_index = index

        if self.survey_id is None:
            self.explore_widget.tabWidget.setCurrentIndex(1)
            self.explore_widget.tabWidget.setEnabled(False)
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
            if self.explore_widget.tabWidget.currentIndex() == 0:
                self.explore_widget.tabWidget.setCurrentIndex(1)
            self.explore_widget.tabWidget.setEnabled(True)

            self.data_to_ui()
            self.draw_map()
            self.load_thumbnails()
            self.load_marks()

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

    def survey_col(self, column):
        survey = self.survey()
        if column in survey:
            column_ = survey[column]
            return str(column_)
        else:
            return ""

    def survey(self):
        return state.model.surveys_data[self.survey_id]

    def is_modified(self):
        if self.survey_id is None:
            return False
        return self.survey_col("site") != self.metadata_widget.ed_site.text() or \
            self.survey_col("operator") != self.metadata_widget.ed_operator.text() or \
            self.survey_col("observer") != self.metadata_widget.ed_observer.text() or \
            self.survey_col("vessel") != self.metadata_widget.ed_vessel.text() or \
            self.survey_col("sea") != self.metadata_widget.cb_sea.currentText() or \
            self.survey_col("wind") != self.metadata_widget.cb_wind.currentText() or \
            self.survey_col("cloud") != self.metadata_widget.cb_cloud.currentText() or \
            self.survey_col("visibility") != self.metadata_widget.cb_vis.currentText() or \
            self.survey_col("comments") != self.metadata_widget.ed_comments.toPlainText() or \
            self.survey_col("tide") != self.metadata_widget.cb_tide.currentText() or \
            self.survey_col("friendly_name") != self.metadata_widget.ed_name.text()

    def ui_to_data(self):
        if self.thumbnail_model is not None:
            self.thumbnail_model.interrupt()

        if self.survey_id is not None:
            self.survey()["site"] = self.metadata_widget.ed_site.text()
            self.survey()["operator"] = self.metadata_widget.ed_operator.text()
            self.survey()["observer"] = self.metadata_widget.ed_observer.text()
            self.survey()["vessel"] = self.metadata_widget.ed_vessel.text()
            self.survey()["sea"] = self.metadata_widget.cb_sea.currentText()
            self.survey()["wind"] = self.metadata_widget.cb_wind.currentText()
            self.survey()["cloud"] = self.metadata_widget.cb_cloud.currentText()
            self.survey()["visibility"] = self.metadata_widget.cb_vis.currentText()
            self.survey()["comments"] = self.metadata_widget.ed_comments.toPlainText()
            self.survey()["tide"] = self.metadata_widget.cb_tide.currentText()
            self.survey()["friendly_name"] = self.metadata_widget.ed_name.text()

            save_survey(self.survey(), state.config.data_folder, state.config.backup_data_folder)

    def data_to_ui(self):
        if self.survey_id is not None:
            self.metadata_widget.ed_site.setText(self.survey_col("site"))
            self.metadata_widget.ed_name.setText(self.survey_col("friendly_name"))
            self.metadata_widget.ed_operator.setText(self.survey_col("operator"))
            self.metadata_widget.ed_observer.setText(self.survey_col("observer"))
            self.metadata_widget.ed_vessel.setText(self.survey_col("vessel"))
            self.metadata_widget.cb_sea.setCurrentText(self.survey_col("sea"))
            self.metadata_widget.cb_wind.setCurrentText(self.survey_col("wind"))
            self.metadata_widget.cb_cloud.setCurrentText(self.survey_col("cloud"))
            self.metadata_widget.cb_vis.setCurrentText(self.survey_col("visibility"))
            self.metadata_widget.cb_tide.setCurrentText(self.survey_col("tide"))
            self.metadata_widget.ed_comments.setPlainText(self.survey_col("comments"))

            self.info_widget.lb_sequence_name.setText(self.survey_col("id"))
            self.info_widget.lb_start_time.setText(utc_to_local(self.survey_col("start_date"), timezone=self.time_zone))
            self.info_widget.lb_end_time.setText(utc_to_local(self.survey_col("finish_date"), timezone=self.time_zone))
            self.info_widget.lb_start_waypoint.setText(f"{self.survey_col('start_lon')} {self.survey_col('start_lat')}")
            self.info_widget.lb_end_waypoint.setText(f"{self.survey_col('finish_lon')} {self.survey_col('finish_lat')}")
            self.explore_widget.folder_label.setText(self.survey_col('json_folder'))
            survey_stats = SurveyStats()
            survey_stats.calculate(self.survey())
            self.survey_stats_to_ui(survey_stats)

    def survey_stats_to_ui(self, survey_stats):
        self.info_widget.lb_number_images.setText(str(survey_stats.photos))
        self.info_widget.lbl_missing_gps.setText(str(survey_stats.missing_gps))
        self.info_widget.lbl_missing_ping.setText(str(survey_stats.missing_ping_depth))
        self.info_widget.lbl_missing_pressure.setText(str(survey_stats.missing_pressure_depth))

    def load_thumbnails(self):
        list_thumbnails:QListView = self.explore_widget.lv_thumbnails
        list_thumbnails.setViewMode(QListWidget.IconMode)
        list_thumbnails.setIconSize(QSize(200, 200))
        list_thumbnails.setResizeMode(QListWidget.Adjust)
        if self.survey_id is not None:
            folder = self.survey_col('image_folder')
            samba = self.survey()["samba"]
            file_ops = get_file_ops(samba)
            photos = [name for name in file_ops.listdir(folder) if name.lower().endswith(".jpg") or name.lower().endswith(".jpeg")]
            self.thumbnail_model = LazyListModel(photos, folder, self.survey_id, samba)
            list_thumbnails.setModel(self.thumbnail_model)

    def load_explore_surveys_tree(self, aims_status_dialog):
        self.ui_to_data()

        state.config.camera_connected = False
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)
        tree = self.explore_widget.surveysTree
        self.surveys_tree_model = make_tree_model(timezone=self.time_zone, include_camera=False, checkable=False)
        tree.setModel(self.surveys_tree_model)
        tree.expandRecursively(self.surveys_tree_model.invisibleRootItem().index(), 3)
        self.explore_widget.surveysTree.selectionModel().selectionChanged.connect(self.explore_tree_selection_changed)
        self.survey_id = None

    def draw_map(self):
        if self.survey_id is not None:
            folder = self.survey_col('image_folder')
            html_str = map_html_str(folder, False)
            # print (html_str)
            if html_str is not None:
                view:QWebEngineView = self.explore_widget.mapView
                view.setHtml(html_str)

    def non_survey_to_stats_ui(self, name):
        self.info_widget.lb_sequence_name.setText(name)
        self.info_widget.lb_start_time.setText("")
        self.info_widget.lb_end_time.setText("")
        self.info_widget.lb_start_waypoint.setText("")
        self.info_widget.lb_end_waypoint.setText("")


