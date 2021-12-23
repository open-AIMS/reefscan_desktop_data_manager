import io
from aims import state
from reefscanner.basic_model.samba import file_ops_factory

from PIL import Image
from PyQt5.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, \
    QThread
from PyQt5.QtGui import QIcon, QImage, QPixmap
import piexif
from PyQt5.QtWidgets import QApplication
import os.path


def image_to_byte_array(image:Image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr


def read_local_file(file):
    with open(file, 'rb') as file_t:
        blob_data = bytearray(file_t.read())
    return blob_data


def read_file(file, samba):
    file_ops = file_ops_factory.get_file_ops(samba)
    with file_ops.open(file, 'rb') as file_t:
        blob_data = bytearray(file_t.read())
    return blob_data


def thumbnail_from_disk_cache(folder, id, photo, samba):
    thumbnail_folder = state.config.data_folder + "/thumbnails/" + id
    os.makedirs(thumbnail_folder, exist_ok=True)
    thumbnail_file = thumbnail_folder + "/" + photo
    if os.path.isfile(thumbnail_file):
        thumbnail = read_local_file(thumbnail_file)
    else:
        orig_file = folder + "/" + photo
        _bytes = read_file(orig_file, samba)
        image = Image.open(io.BytesIO(_bytes))
        image.thumbnail(size=(100, 100))
        image.save(thumbnail_file)
        thumbnail = image_to_byte_array(image)

    return thumbnail


def thumbnail_from_exif(filename):
    exif_dict = piexif.load(filename)
    thumbnail = exif_dict.pop('thumbnail')
    if thumbnail is None:
        # print ("no thumbnail")
        image = Image.open(filename)
        image.thumbnail(size=(100, 100))
        thumbnail = image_to_byte_array(image)
        exif_dict["thumbnail"] = thumbnail
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filename)
    # else:
        # print ("Got a thumbnail")
    return thumbnail


class NameAndIcon:
    def __init__(self, name: str, icon: QIcon, full_path):
        self.name = name
        self.icon = icon
        self.full_path = full_path


class ThumbnailMaker(QThread):
    add_thumbnail = pyqtSignal(NameAndIcon)

    def __init__(self, photos, folder, id, samba):
        super().__init__()
        self.photos = photos
        self.folder = folder
        self.id = id
        self.interrupted = False
        self.samba = samba

    def run(self):
        # Your long-running task goes here ...
        for photo in self.photos:
            if self.interrupted:
                return
            full_path = self.folder + "/" + photo
            # try:
            thumbnail = thumbnail_from_disk_cache(self.folder, self.id, photo, self.samba)
            pixmap = QPixmap()
            pixmap.loadFromData(thumbnail)
            icon = QIcon(pixmap)
            # except:
            #     icon = None
            name_and_icon = NameAndIcon(photo, icon, full_path)
            self.add_thumbnail.emit(name_and_icon)


class LazyListModel (QAbstractListModel):
    numberPopulated = pyqtSignal(int)

    def __init__(self, all_items, folder, id, samba):
        super().__init__()
        self.all_items = all_items
        self.icons = []
        self.total_count = len(self.all_items)
        self.loaded_count = 0
        self.folder = folder
        self.thumbnails = []
        self.thumbnailMaker = ThumbnailMaker(self.all_items, folder, id, samba)
        self.thumbnailMaker.add_thumbnail.connect(self.add_thumbnail)
        # print("start now")
        self.thumbnailMaker.start()
        # print("ok started")


    def interrupt(self):
        self.thumbnailMaker.interrupted = True
        self.thumbnailMaker.quit()


    @pyqtSlot(NameAndIcon)
    def add_thumbnail(self, thumbnail):
        # print(thumbnail.name)
        self.thumbnails.append(thumbnail)

    def rowCount(self, index: QModelIndex):
        # print("rowcount")
        if index.isValid():
            return 0
        else:
            return self.loaded_count

    def data(self, index: QModelIndex, role):
        # print("data")
        if not index.isValid():
            return QVariant()

        if index.row() >= self.loaded_count or index.row() < 0:
            return QVariant()

        if role == Qt.DisplayRole:
            name = self.thumbnails[index.row()].name
            # print(name)
            return name

        if role == Qt.DecorationRole:
            return self.thumbnails[index.row()].icon

        if role == Qt.UserRole:
            return self.thumbnails[index.row()].full_path

        return QVariant()

    def canFetchMore(self, parent: QModelIndex):
        # print ("canFetchMore")
        if parent.isValid():
            return False

        ret_val = self.loaded_count < self.total_count
        return ret_val

    def fetchMore(self, parent: QModelIndex):
        # print ("fetchMore")
        if parent.isValid():
            return

        items_to_fetch = 0
        while items_to_fetch <= 0:
            QApplication.processEvents()
            new_count = len(self.thumbnails)
            items_to_fetch = new_count - self.loaded_count
            # print(items_to_fetch)

        self.beginInsertRows(QModelIndex(), self.loaded_count, new_count)

        self.loaded_count = new_count

        self.endInsertRows()

        self.numberPopulated.emit(items_to_fetch)

