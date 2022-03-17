import logging
import os
import sys

import shortuuid

from aims import state
from aims.gui_model.lazy_list_model import LazyListModel
from aims.ui.map_html import map_html_str
import PyQt5.QtWebEngineWidgets
from PyQt5 import QtWidgets, uic, QtLocation, QtPositioning
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QAbstractItemModel, QItemSelectionModel, QUrl, QSize
from PyQt5.QtGui import QStandardItemModel, QIcon
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QTreeView, QWidget, QComboBox, QApplication, QListWidget, QListWidgetItem, QListView, \
    QMessageBox, QTextEdit, QPlainTextEdit
from reefscanner.basic_model.reader_writer import save_survey, save_site
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.config import Config
from aims.gui_model.SurveyTreeModel import SurveyTreeModel
from aims.gui_model.model import GuiModel
from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.load_data import load_data
from aims.operations.sync_from_hardware_operation import SyncFromHardwareOperation
from aims.ui.checked_tree_item import CheckTreeitem

logger = logging.getLogger(__name__)


def find_in_tree(model: QAbstractItemModel, name_to_find, parent: QModelIndex = QModelIndex()):
    for r in range(model.rowCount(parent)):
        index = model.index(r, 0, parent)
        name = model.data(index)
        if name == name_to_find:
            return index
        # // here is your applicable code
        if model.hasChildren(index):
            r = find_in_tree(model, name_to_find, index)
            if r is not None:
                return r
    return None


class SurveysTree(object):
    def __init__(self):
        super().__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.start_ui = f'{state.meipass}resources/surveys-tree.ui'

        self.ui = uic.loadUi(self.start_ui)
        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)
        self.aims_status_dialog = AimsStatusDialog(self.ui)
        self.all_surveys = {}
        self.survey_id = None
        self.clipboard = None
        self.tree_model: QStandardItemModel = None

        self.ui.btnMap.clicked.connect(self.toggle_map)
        self.ui.btnInfo.clicked.connect(self.toggle_info)
        self.ui.btn_thumbnails.clicked.connect(self.toggle_thumbnails)
        self.ui.btn_upload.clicked.connect(self.upload)
        self.ui.btn_copy.clicked.connect(self.copy)
        self.ui.btn_paste.clicked.connect(self.paste)
        self.ui.widEdit.setVisible(False)
        self.ui.widInfo.setVisible(False)
        self.ui.widMap.setVisible(False)
        self.ui.wid_thumbnails.setVisible(False)
        self.ui.btnAddSite.clicked.connect(self.make_site)
        self.ui.cb_site.currentIndexChanged.connect(self.site_changed)
        self.has_site_changed = False
        self.thumbnail_model = None
        self.ed_comments: QTextEdit = self.ui.ed_comments
        lv_thumbnails:QListView = self.ui.lv_thumbnails
        lv_thumbnails.doubleClicked.connect(self.click_photo)

    def checked_surveys(self, parent: QModelIndex = QModelIndex()):
        model = self.tree_model
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

    def click_photo(self, index: QModelIndex):
        os.startfile(index.data(role=Qt.UserRole))

    def show(self):
        self.ui.show()
        self.add_tree_data(None)
        self.lookups()

        self.data_to_ui()
        self.show_messages()

    def show_messages(self):
        txt_messages: QTextEdit = self.ui.txtMessages
        txt_messages.setVisible(len(state.model.messages) > 0)
        txt_messages.clear()
        txt_messages.append('Messages:')
        for message in state.model.messages:
            txt_messages.append("    " + message)

        size: QSize = txt_messages.document().size().toSize()
        txt_messages.setFixedHeight(size.height() + 3)

    def survey(self):
        return self.all_surveys[self.survey_id]

    def site_changed(self):
        self.has_site_changed = True

    def copy(self):
        self.ui_to_data()
        self.clipboard = self.survey()

    def paste(self):
        if self.clipboard is not None:
            self.ui_to_data()
            if self.survey()["site"] == "":
                self.survey()["site"] = self.clipboard["site"]

            if self.survey()["operator"] == "":
                self.survey()["operator"] = self.clipboard["operator"]

            if self.survey()["observer"] == "":
                self.survey()["observer"] = self.clipboard["observer"]

            if self.survey()["vessel"] == "":
                self.survey()["vessel"] = self.clipboard["vessel"]

            if self.survey()["sea"] == "":
                self.survey()["sea"] = self.clipboard["sea"]

            if self.survey()["wind"] == "":
                self.survey()["wind"] = self.clipboard["wind"]

            if self.survey()["cloud"] == "":
                self.survey()["cloud"] = self.clipboard["cloud"]

            if self.survey()["visibility"] == "":
                self.survey()["visibility"] = self.clipboard["visibility"]

            self.data_to_ui()
            save_survey(self.survey())

    def upload(self):
        self.ui_to_data()
        surveys = self.checked_surveys()


        # # self.model.add_new_sites(self.hardware_sync_model.new_sites)
        # surveys_folder = f"{state.model.data_folder}/images"
        # os.makedirs(surveys_folder, exist_ok=True)
        # for survey in state.model.camera_surveys.values():
        #     survey_id = survey["id"]
        #     survey["folder"] = f"{surveys_folder}/{survey_id}"
        #     survey["trip"] = state.model.trip["uuid"]
        #     save_survey(survey)
        #
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
        state.load_data_model(aims_status_dialog=self.aims_status_dialog)
        self.add_tree_data(None)

    def lookups(self):
        self.site_lookup()

        self.ui.cb_tide.addItem("")
        self.ui.cb_tide.addItem("Falling")
        self.ui.cb_tide.addItem("High")
        self.ui.cb_tide.addItem("Low")
        self.ui.cb_tide.addItem("Rising")

        self.ui.cb_sea.addItem("")
        self.ui.cb_sea.addItem("calm")
        self.ui.cb_sea.addItem("slight")
        self.ui.cb_sea.addItem("moderate")
        self.ui.cb_sea.addItem("rough")

        self.ui.cb_wind.addItem("")
        self.ui.cb_wind.addItem("<5")
        self.ui.cb_wind.addItem("5-10")
        self.ui.cb_wind.addItem("10-15")
        self.ui.cb_wind.addItem("15-20")
        self.ui.cb_wind.addItem("20-25")
        self.ui.cb_wind.addItem("25-30")
        self.ui.cb_wind.addItem(">30")

        self.ui.cb_cloud.addItem("")
        self.ui.cb_cloud.addItem("1")
        self.ui.cb_cloud.addItem("2")
        self.ui.cb_cloud.addItem("3")
        self.ui.cb_cloud.addItem("4")
        self.ui.cb_cloud.addItem("5")
        self.ui.cb_cloud.addItem("6")
        self.ui.cb_cloud.addItem("7")
        self.ui.cb_cloud.addItem("8")

        self.ui.cb_vis.addItem("")
        self.ui.cb_vis.addItem("<5")
        self.ui.cb_vis.addItem("5-10")
        self.ui.cb_vis.addItem("10-15")
        self.ui.cb_vis.addItem("15-20")
        self.ui.cb_vis.addItem("20-25")
        self.ui.cb_vis.addItem("25-30")
        self.ui.cb_vis.addItem(">30")

    def site_lookup(self):
        cb_site: QComboBox = self.ui.cb_site
        lookup = state.model.surveysModel.sites_lookup.items()
        for key, value in sorted(lookup, key=lambda item: item[1]):
            cb_site.addItem(value, key)

    def ui_to_data(self):
        if self.survey_id is not None:
            cb_site: QComboBox = self.ui.cb_site
            self.survey()["site"] = cb_site.currentData()
            self.survey()["operator"] = self.ui.ed_operator.text()
            self.survey()["observer"] = self.ui.ed_observer.text()
            self.survey()["vessel"] = self.ui.ed_vessel.text()
            self.survey()["sea"] = self.ui.cb_sea.currentText()
            self.survey()["wind"] = self.ui.cb_wind.currentText()
            self.survey()["cloud"] = self.ui.cb_cloud.currentText()
            self.survey()["visibility"] = self.ui.cb_vis.currentText()
            self.survey()["comments"] = self.ed_comments.toPlainText()
            self.survey()["tide"] = self.ui.cb_tide.currentText()
            self.survey()["friendly_name"] = self.ui.ed_name.text()

            save_survey(self.survey())

    def data_to_ui(self):
        if self.survey_id is not None:
            self.ui.widEdit.setVisible(True)
            cb_site: QComboBox = self.ui.cb_site
            cb_site.setCurrentIndex(cb_site.findData(self.survey_col("site")))
            self.ui.ed_name.setText(self.survey_col("friendly_name"))
            self.ui.ed_operator.setText(self.survey_col("operator"))
            self.ui.ed_observer.setText(self.survey_col("observer"))
            self.ui.ed_vessel.setText(self.survey_col("vessel"))
            self.ui.cb_sea.setCurrentText(self.survey_col("sea"))
            self.ui.cb_wind.setCurrentText(self.survey_col("wind"))
            self.ui.cb_cloud.setCurrentText(self.survey_col("cloud"))
            self.ui.cb_vis.setCurrentText(self.survey_col("visibility"))
            self.ui.cb_tide.setCurrentText(self.survey_col("tide"))

            self.ui.lb_sequence_name.setText(self.survey_col("id"))
            self.ui.lb_number_images.setText(self.survey_col("photos"))
            self.ui.lb_start_time.setText(self.survey_col("start_date"))
            self.ui.lb_end_time.setText(self.survey_col("finish_date"))
            self.ui.lb_start_waypoint.setText(f"{self.survey_col('start_lon')} {self.survey_col('start_lat')}")
            self.ui.lb_end_waypoint.setText(f"{self.survey_col('finish_lon')} {self.survey_col('finish_lat')}")
            self.ui.lb_number_images.setText(self.survey_col("photos"))
            self.ed_comments.setPlainText(self.survey_col("comments"))

        else:
            self.ui.widEdit.setVisible(False)

    def survey_col(self, column):
        survey = self.survey()
        if column in survey:
            column_ = survey[column]
            return str(column_)
        else:
            return ""

    def toggle_map(self):
        wid_map: QWidget = self.ui.widMap
        wid_map.setVisible(not wid_map.isVisible())
        self.draw_map()

    def draw_map(self):
        if self.ui.widMap.isVisible() and self.survey_id is not None:
            folder = self.survey_col('image_folder')
            html_str = map_html_str(folder, self.survey()["samba"])
            if html_str is not None:
                self.ui.webEngineView.setHtml(html_str)

    def toggle_info(self):
        wid_info: QWidget = self.ui.widInfo
        wid_info.setVisible(not wid_info.isVisible())

    def toggle_thumbnails(self):
        wid_thumbnails: QWidget = self.ui.wid_thumbnails
        wid_thumbnails.setVisible(not wid_thumbnails.isVisible())
        self.load_thumbnails()

    def load_thumbnails(self):
        list_thumbnails:QListView = self.ui.lv_thumbnails
        list_thumbnails.setViewMode(QListWidget.IconMode)
        list_thumbnails.setIconSize(QSize(200, 200))
        list_thumbnails.setResizeMode(QListWidget.Adjust)
        if self.ui.wid_thumbnails.isVisible() and self.survey_id is not None:
            folder = self.survey_col('image_folder')
            samba = self.survey()["samba"]
            file_ops = get_file_ops(samba)
            photos = [name for name in file_ops.listdir(folder) if name.lower().endswith(".jpg") or name.lower().endswith(".jpeg")]
            self.thumbnail_model = LazyListModel(photos, folder, self.survey_id, samba)
            list_thumbnails.setModel(self.thumbnail_model)
            # self.thumbnail_model.interrupted = False
            # photos = photos[0:20]
            # for photo in photos:
            #     list_thumbnails.addItem(QListWidgetItem(QIcon(folder + "/" + photo), photo));


    def add_tree_data(self, selected_row):
        print("add tree data")
        self.tree_model = QStandardItemModel()

        duplicate_ids = state.model.surveys_data.keys() & state.model.camera_surveys.keys()
        if len(duplicate_ids) > 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Conflict Warning")
            msg.setInformativeText("Surveys on the camera conflict with local surveys.")
            msg.setWindowTitle("Conflict Warning")
            msg.setDetailedText("This is probably the result of an incomplete upload. The local images will be ignored until the upload is complete.")
            msg.exec_()

        self.all_surveys = {}
        self.all_surveys.update(state.model.surveys_data)
        self.all_surveys.update(state.model.camera_surveys)

        self.tree_model.itemChanged.connect(self.on_itemChanged)
        view: QTreeView = self.ui.treeView
        view.setHeaderHidden(True)
        view.setModel(self.tree_model)
        view.selectionModel().selectionChanged.connect(self.selection_changed)

        camera_branch = self.make_branch(state.model.camera_surveys, 'Reefscan Camera', checkable=True)
        local_branch = self.make_branch(state.model.surveys_data, 'Local Drive', checkable=False)

        self.tree_model.appendRow(camera_branch)
        self.tree_model.appendRow(local_branch)

        view.expandAll()

        # print(selected_row)

        # if selected_row is not None:
            # row_found = find_in_tree(tree_model, selected_row)
            # print(row_found)
            # view.selectionModel().setCurrentIndex(row_found, QItemSelectionModel.Current)
            # view.scrollTo(row_found)

    def make_branch(self, survey_data, name, checkable):
        survey_tree_model = SurveyTreeModel(survey_data, state.model.surveysModel.sites_lookup)
        branch = CheckTreeitem(name, checkable)
        sites = survey_tree_model.sites
        for site in sites.keys():
            site_branch = CheckTreeitem(site, checkable)
            branch.appendRow(site_branch)

            surveys = sites[site]
            for survey_id in surveys:
                survey_branch = CheckTreeitem(survey_id, checkable)
                survey_branch.setData(survey_id, Qt.UserRole)
                site_branch.appendRow(survey_branch)
        return branch

    def selection_changed(self,  item_selection:QItemSelection):
        if self.thumbnail_model is not None:
            self.thumbnail_model.interrupt()
        # print ("Selection change")
        self.ui_to_data()

        # print (item_selection)
        for index in item_selection.indexes():
            self.survey_id = index.data(Qt.UserRole)
            # print(self.survey_id)

        if self.has_site_changed:
            self.add_tree_data(self.survey_id)

        self.data_to_ui()
        self.draw_map()
        self.load_thumbnails()
        self.has_site_changed = False

    def make_site(self):
        input_box = QtWidgets.QInputDialog()
        input_box.setLabelText("Site Name")
        if "start_lat" not in self.survey() or "start_lon" not in self.survey():
            raise Exception("Cannot not make a site for this survey. No geographic data exists. Is the slow_network check box ticked?")

        result = input_box.exec_()
        if result == QtWidgets.QDialog.Accepted:
            site_name = input_box.textValue()

            self.new_site_for_survey(site_name)
            self.data_to_ui()

    def new_site_for_survey(self, site_name):
        site_id = shortuuid.uuid()
        survey = self.survey()
        site = {"uuid": site_id, "name": site_name,
                "latitude": survey["start_lat"], "longitude": survey["start_lon"]
                }
        state.model.add_new_site(site)
        state.model.surveysModel.sites_lookup[site_id] = site_name
        self.site_lookup()
        survey["site"] = site_id

        save_survey(survey)

    # @pyqtSlot(QStandardItem)
    def on_itemChanged(self,  item):
        # print ("Item change")
        item.cascade_check()

