from PyQt5.QtCore import QObject, QItemSelection, Qt, QRect, QByteArray
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QHeaderView, QTableView, QAbstractItemView, QLabel

from aims.model.cots_detection import CotsDetection
from aims.model.cots_detection_list import CotsDetectionList
from aims.model.proportional_rectangle import ProportionalRectangle


# This class handles the visualisation of COTS detections as a table
# it shows photos of COTS for each COTS sequence
from aims.utils import read_binary_file_support_samba


class CotsDisplayComponent(QObject):
    def __init__(self, realtime_cots_widget):
        super().__init__()
        self.realtime_cots_detection_list = CotsDetectionList()
        self.realtime_cots_widget = realtime_cots_widget
        self.item_model = QStandardItemModel(self)
        self.photos=None
        self.selected_photo = 0
        self.sequence_id = None
        self.realtime_cots_widget.button_next.clicked.connect(self.next)
        self.realtime_cots_widget.button_previous.clicked.connect(self.previous)

    # detect and display  cots in all of the photos for the currently selected survey
    # This could be from the disk or the camera (samba = True for camera data)
    def display_realtime_detections(self, folder, samba):
        # read_realtime_files returns true if the data is changes
        # If it is not changed don't do anything
        if self.realtime_cots_detection_list.read_realtime_files(folder, samba):


            self.item_model.clear()

            # Create a QStandardItemModel
            self.item_model.setHorizontalHeaderLabels(["Sequence ID", "Class ID", "Maximum Score"])
            row: CotsDetection
            for row in self.realtime_cots_detection_list.cots_detections_list:
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

            table_view: QTableView = self.realtime_cots_widget.tableView
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

    # Show the current photo, highlight the COTS and enable the appropriate buttons
    # This could be from the disk or the camera so we need to allow for that
    def show_photo(self):
        if self.photos is None:
            return

        photo = self.photos[self.selected_photo]
        label_photo: QLabel = self.realtime_cots_widget.label_photo

        # determine the width available to display the photo
        available_width = label_photo.width()

        file_contents: bytes = read_binary_file_support_samba(photo, self.realtime_cots_detection_list.samba)
        image = QImage()
        image.loadFromData(file_contents, format='JPG')
        image_width = image.width()
        image_height = image.height()
        pixmap = QPixmap.fromImage(image)

        # Get rectangles for all the COTS in the photo
        rectangles = self.realtime_cots_detection_list.image_rectangles_by_filename[photo]
        self.draw_rectangles(pixmap, image_height, image_width, rectangles)

        pixmap = pixmap.scaled(available_width, 99999, aspectRatioMode=Qt.KeepAspectRatio)

        self.realtime_cots_widget.label_photo.setPixmap(pixmap)
        self.realtime_cots_widget.label_photo.show()

        # enable appropriate buttons
        self.realtime_cots_widget.button_next.setEnabled(self.selected_photo < len(self.photos)-1)
        self.realtime_cots_widget.button_previous.setEnabled(self.selected_photo > 0)

    # Draw the rectangles over the photo
    # The cots for the current sequence will have a red rectangle. Yellow rectangles for the others
    def draw_rectangles(self, pixmap, image_height, image_width, proportional_rectangles):
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(10)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        rectangle: ProportionalRectangle
        for proportional_rectangle in proportional_rectangles:
            if proportional_rectangle.sequence_id == self.sequence_id:
                pen.setColor(Qt.red)
            else:
                pen.setColor(Qt.yellow)
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

