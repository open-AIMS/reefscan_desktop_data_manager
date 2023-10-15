import logging

from PyQt5.QtCore import QObject, QItemSelection, Qt, QRect, QByteArray
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QHeaderView, QTableView, QAbstractItemView, QLabel, QCheckBox

from aims import utils
from aims.model.cots_detection import CotsDetection
from aims.model.cots_detection_list import CotsDetectionList
from aims.model.proportional_rectangle import ProportionalRectangle


# This class handles the visualisation of COTS detections as a table
# it shows photos of COTS for each COTS sequence
from aims.utils import read_binary_file_support_samba
logger = logging.getLogger("CotsDisplayComponent")


class CotsDisplayComponent(QObject):
    def __init__(self, cots_widget):
        super().__init__()
        self.realtime_cots_detection_list = CotsDetectionList()
        self.eod_cots_detection_list = CotsDetectionList()
        self.cots_detection_list = None
        self.cots_widget = cots_widget
        self.item_model = QStandardItemModel(self)
        self.photos=None
        self.selected_photo = 0
        self.sequence_id = None
        self.cots_widget.button_next.clicked.connect(self.next)
        self.cots_widget.button_previous.clicked.connect(self.previous)
        eod_check_box: QCheckBox = self.cots_widget.eod_check_box
        eod_check_box.stateChanged.connect(self.create_cots_detections_table)
        self.cots_widget.refreshButton.clicked.connect(self.create_cots_detections_table)
        self.cots_widget.openPhotoButton.clicked.connect(self.open_photo)

    def create_cots_detections_table(self):
        eod_check_box: QCheckBox = self.cots_widget.eod_check_box
        if eod_check_box.checkState() == Qt.Checked:
            self.cots_detection_list = self.eod_cots_detection_list
        else:
            self.cots_detection_list = self.realtime_cots_detection_list

        try:
            minimum_score = float(self.cots_widget.minimumScoreTextBox.text())
        except Exception as e:
            logger.warn("error getting minimum score", e)
            minimum_score = 0

        if self.cots_detection_list.has_data:
            # Create a QStandardItemModel
            self.item_model.clear()
            # self.clear_photo()
            self.item_model.setHorizontalHeaderLabels(["Sequence", "Class", "Score"])
            row: CotsDetection
            for row in self.cots_detection_list.cots_detections_list:
                if row.best_score > minimum_score:
                    sequence_id_item = QStandardItem(str(row.sequence_id))
                    class_item = QStandardItem(str(row.best_class))
                    score_item = QStandardItem(str(row.best_score))
                    sequence_id_item.setData(row, Qt.UserRole)
                    class_item.setData(row, Qt.UserRole)
                    score_item.setData(row, Qt.UserRole)
                    self.item_model.appendRow([sequence_id_item,
                                                class_item,
                                                score_item,
                                                ])

            table_view: QTableView = self.cots_widget.tableView
            table_view.setModel(self.item_model)
            table_view.setSelectionMode(QAbstractItemView.SingleSelection)
            table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_view.selectionModel().currentChanged.connect(self.selection_changed)

    def read_data(self, folder, samba):

        self.realtime_cots_detection_list.read_realtime_files(folder, samba)
        if samba:
            self.eod_cots_detection_list.has_data = False
        else:
            self.eod_cots_detection_list.read_eod_files(folder, samba)

        self.create_cots_detections_table()


    # When the user selects a row in the table, the photos for that sequence are displayed
    def selection_changed(self, current, previous):
        current_data: CotsDetection = self.item_model.data(current, Qt.UserRole)
        self.sequence_id = current_data.sequence_id
        self.photos = current_data.images
        self.selected_photo = 0
        self.show_photo()

# TODO not working need to google this when I have internet
    def clear_photo(self):
        self.cots_widget.label_photo.setPixmap(None)
        self.cots_widget.label_photo.show()

    # Show the current photo, highlight the COTS and enable the appropriate buttons
    # This could be from the disk or the camera so we need to allow for that
    def show_photo(self):
        if self.photos is None:
            return

        photo = self.photos[self.selected_photo]
        label_photo: QLabel = self.cots_widget.label_photo

        # determine the width available to display the photo
        available_width = label_photo.width()

        file_contents: bytes = read_binary_file_support_samba(photo, self.cots_detection_list.samba)
        image = QImage()
        image.loadFromData(file_contents, format='JPG')
        image_width = image.width()
        image_height = image.height()
        pixmap = QPixmap.fromImage(image)

        # Get rectangles for all the COTS in the photo
        rectangles = self.cots_detection_list.image_rectangles_by_filename[photo]
        self.draw_rectangles(pixmap, image_height, image_width, rectangles)

        pixmap = pixmap.scaled(available_width, 99999, aspectRatioMode=Qt.KeepAspectRatio)

        self.cots_widget.label_photo.setPixmap(pixmap)
        self.cots_widget.label_photo.show()

        # enable appropriate buttons
        self.cots_widget.button_next.setEnabled(self.selected_photo < len(self.photos)-1)
        self.cots_widget.button_previous.setEnabled(self.selected_photo > 0)

        self.cots_widget.label_photo.setAlignment(Qt.AlignCenter)

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

