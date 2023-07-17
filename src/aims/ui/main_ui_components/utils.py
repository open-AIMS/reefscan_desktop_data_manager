from PyQt5.QtCore import QDir, QStandardPaths
from PyQt5.QtWidgets import QFileSystemModel

from aims.state import state


def split_drive(dir_name):
    dir2 = dir_name.replace("/", "\\")
    drive = dir2[:3]
    rest = dir2[3:]
    return drive, rest


def setup_file_system_tree_and_combo_box(drive_combo_box, tree, selected_folder, fixed_drives):
    data_drive, data_folder_only = split_drive(selected_folder)
    for drive in fixed_drives:
        drive_combo_box.addItem(drive["label"], drive["letter"])
    drive_combo_box.setCurrentText(data_drive)

    if data_drive in fixed_drives:
        setup_folder_tree(data_drive, tree)
        tree.setCurrentIndex(
            tree.model().index(selected_folder))
    else:
        setup_folder_tree(fixed_drives[0], tree)


def setup_folder_tree(drive, tree):
    file_model = QFileSystemModel()
    file_model.setRootPath(drive)
    file_model.setFilter(QDir.AllDirs | QDir.NoDot | QDir.NoDotDot)
    file_model.setRootPath(QStandardPaths.displayName(QStandardPaths.DesktopLocation))
    tree.setModel(file_model)
    tree.setRootIndex(file_model.index(drive))
    for i in range(1, tree.model().columnCount()):
        tree.header().hideSection(i)


def update_data_folder_from_tree(tree):
    selected = tree.selectedIndexes()
    if len(selected) > 0:
        index = selected[0]
        item = tree.model().filePath(index)
        state.config.data_folder = str(item)
    else:
        raise Exception("Please select a folder")

def clearLayout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clearLayout(item.layout())
