import logging
import os

from PyQt5.QtCore import QObject, QItemSelection, Qt, QRect, QByteArray
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QHeaderView, QTableView, QAbstractItemView, QLabel, QCheckBox, QSizePolicy

from aims import utils
from aims.model.cots_detection import CotsDetection
from aims.model.proportional_rectangle import ProportionalRectangle

from functools import partial

# This class handles the visualisation of COTS detections as a table
# it shows photos of COTS for each COTS sequence
from aims.utils import read_binary_file_support_samba
logger = logging.getLogger("CotsDisplayComponent")


class CotsDisplayComponent(QObject):
    def __init__(self, cots_widget, cots_display_params):
        super().__init__()
        self.cots_widget = cots_widget
        self.item_model = QStandardItemModel(self)
        self.photos=None
        self.selected_photo = 0
        self.sequence_id = None
        self.only_show_confirmed: bool = False
        self.cots_widget.button_next.clicked.connect(self.next)
        self.cots_widget.button_previous.clicked.connect(self.previous)
        eod_check_box: QCheckBox = self.cots_widget.eod_check_box
        eod_check_box.stateChanged.connect(self.create_cots_detections_table)
        confirmed_check_box: QCheckBox = self.cots_widget.confirmed_check_box
        confirmed_check_box.stateChanged.connect(self.confirmed_check_box_state_changed)
        self.cots_widget.refreshButton.clicked.connect(self.create_cots_detections_table)
        self.cots_widget.openPhotoButton.clicked.connect(self.open_photo)
        self.cots_display_params = cots_display_params

        self.cots_widget.button_yes.clicked.connect(partial(self.confirm_cots_detection, True))
        self.cots_widget.button_no.clicked.connect(partial(self.confirm_cots_detection, False))

    def confirmed_check_box_state_changed(self, state):
        if state == 2: # 2 = Checked, 0 = Unchecked
            self.only_show_confirmed = True
        else:
            self.only_show_confirmed = False
        self.create_cots_detections_table()


    def confirmed_field_to_string(self, cots_detection: CotsDetection):
        if cots_detection.confirmed is None:
            confirmed_string = ''
        else:
            if cots_detection.confirmed:
                confirmed_string = 'Yes'
            else:
                confirmed_string = 'No'
        return confirmed_string
            

    def show(self):
        if self.cots_display_params.eod:
            self.cots_widget.eod_check_box.setCheckState(Qt.Checked)
        else:
            self.cots_widget.eod_check_box.setCheckState(Qt.Unchecked)

        self.cots_widget.minimumScoreTextBox.setText(str(self.cots_display_params.minimum_score))
        self.create_cots_detections_table()
        self.cots_widget.graphicsView.setVisible(False)



    def create_cots_detections_table(self):
        eod_check_box: QCheckBox = self.cots_widget.eod_check_box
        self.cots_display_params.eod = eod_check_box.checkState() == Qt.Checked

        try:
            self.cots_display_params.minimum_score = float(self.cots_widget.minimumScoreTextBox.text())
        except Exception as e:
            logger.warn("error getting minimum score", e)
            self.cots_display_params.minimum_score = 0

        self.item_model.clear()

        if self.cots_display_params.cots_detection_list().has_data:
            self.clear_photo()
            self.item_model.setHorizontalHeaderLabels(["Sequence", "Class", "Score", "Confirmed"])
            row: CotsDetection
            for row in self.cots_display_params.cots_detection_list().cots_detections_list:
                if row.best_score > self.cots_display_params.minimum_score:
                    display_row = self.only_show_confirmed and row.confirmed or not self.only_show_confirmed
                    if display_row:
                        sequence_id_item = QStandardItem(str(row.sequence_id))
                        class_item = QStandardItem(str(row.best_class))
                        score_item = QStandardItem(str(row.best_score))
                        confirmed_item = QStandardItem(self.confirmed_field_to_string(row))
                        sequence_id_item.setData(row, Qt.UserRole)
                        class_item.setData(row, Qt.UserRole)
                        score_item.setData(row, Qt.UserRole)
                        confirmed_item.setData(row, Qt.UserRole)
                        self.item_model.appendRow([sequence_id_item,
                                                    class_item,
                                                    score_item,
                                                    confirmed_item
                                                    ])

            table_view: QTableView = self.cots_widget.tableView
            table_view.setModel(self.item_model)
            table_view.setSelectionMode(QAbstractItemView.SingleSelection)
            table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_view.selectionModel().currentChanged.connect(self.selection_changed)


    # When the user selects a row in the table, the photos for that sequence are displayed
    def selection_changed(self, current, previous):
        current_data: CotsDetection = self.item_model.data(current, Qt.UserRole)
        self.sequence_id = current_data.sequence_id
        self.photos = current_data.images
        self.selected_photo = 0
        self.show_photo()

# TODO not working need to google this when I have internet
    def clear_photo(self):
        table_view:QTableView = self.cots_widget.tableView
        table_view.sizePolicy().setVerticalPolicy(QSizePolicy.Policy.Expanding)
        self.cots_widget.graphicsView.setVisible(False)
        self.cots_widget.button_next.setVisible(False)
        self.cots_widget.button_previous.setVisible(False)


    # Show the current photo, highlight the COTS and enable the appropriate buttons
    # This could be from the disk or the camera so we need to allow for that
    def show_photo(self):
        if self.photos is None:
            return

        table_view:QTableView = self.cots_widget.tableView
        table_view.sizePolicy().setVerticalPolicy(QSizePolicy.Policy.Preferred)
        self.cots_widget.graphicsView.setVisible(True)
        self.cots_widget.button_next.setVisible(True)
        self.cots_widget.button_previous.setVisible(True)


        photo = self.photos[self.selected_photo]
        graphicsView: QLabel = self.cots_widget.graphicsView

        file_contents: bytes = read_binary_file_support_samba(photo, self.cots_display_params.cots_detection_list().samba)
        image = QImage()
        image.loadFromData(file_contents, format='JPG')
        image_width = image.width()
        image_height = image.height()
        pixmap = QPixmap.fromImage(image)

        # Get rectangles for all the COTS in the photo
        rectangles = self.cots_display_params.cots_detection_list().image_rectangles_by_filename[photo]
        self.draw_rectangles(pixmap, image_height, image_width, rectangles)
 
        # self.cots_widget.graphicsView.setPixmap(pixmap.scaled(graphicsView.width(), 99999, aspectRatioMode=Qt.KeepAspectRatio))
        self.cots_widget.graphicsView.setPhoto(pixmap)
        self.cots_widget.graphicsView.show()

        # enable appropriate buttons
        self.cots_widget.button_next.setEnabled(self.selected_photo < len(self.photos)-1)
        self.cots_widget.button_previous.setEnabled(self.selected_photo > 0)

        self.cots_widget.label_file_name.setText(os.path.dirname(photo))

# open the photo in the OS
    def open_photo(self):
        if self.photos is None:
            return

        photo = self.photos[self.selected_photo]
        utils.open_file(photo)

    # Draw the rectangles over the photo
    # The cots for the current sequence will have a red rectangle. Yellow rectangles for the others
    # solid lines for real detections dotted lines for phantom detections
    def draw_rectangles(self, pixmap, image_height, image_width, proportional_rectangles):
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(15)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        rectangle: ProportionalRectangle
        for proportional_rectangle in proportional_rectangles:
            if proportional_rectangle.sequence_id == self.sequence_id:
                if self.current_selection_is_confirmed():
                    pen.setColor(Qt.green)
                else:
                    pen.setColor(Qt.red)
            else:
                pen.setColor(Qt.yellow)

            if proportional_rectangle.phantom:
                pen.setStyle(Qt.DotLine)
            else:
                pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.make_rect(proportional_rectangle, image_width, image_height))
        painter.end()
        return pixmap

    # makes a rectangle of pixel values (integers) given a rectangle of proportions and the dimensions of the image
    def make_rect (self, proportional_rectangle: ProportionalRectangle, image_width: int, image_height: int) -> QRect:
        left = round(proportional_rectangle.left * image_width)
        top = round(proportional_rectangle.top * image_height)
        width = round(proportional_rectangle.width * image_width)
        height = round(proportional_rectangle.height * image_height)
        return QRect(left, top, width, height)


    def next(self):
        self.selected_photo += 1
        self.show_photo()

    def previous(self):
        self.selected_photo -= 1
        self.show_photo()

    def confirm_cots_detection(self, confirmed):
        cots_detection_list = self.cots_display_params.cots_detection_list()
        selected_detection_idx = cots_detection_list.get_index_by_sequence_id(self.sequence_id)
        
        if selected_detection_idx is not None:
            cots_detection_list.cots_detections_list[selected_detection_idx].confirmed = confirmed
            self.create_cots_detections_table()
            self.show_photo()

            if self.current_selection_is_confirmed():
                is_eod = self.cots_widget.eod_check_box.checkState() == Qt.Checked
                cots_detection_list.write_confirmed_field_to_cots_sequence(self.sequence_id, eod=is_eod)


    def current_selection_is_confirmed(self):
        return self.get_confirmed_current_selection() is not None

    def get_confirmed_current_selection(self):
        cots_detection_list = self.cots_display_params.cots_detection_list()

        selected_detection_idx = cots_detection_list.get_index_by_sequence_id(self.sequence_id)
        return cots_detection_list.cots_detections_list[selected_detection_idx].confirmed

        

