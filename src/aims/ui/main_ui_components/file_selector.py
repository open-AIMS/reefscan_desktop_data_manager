from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QPushButton


FILE_SELECTOR_NULL_LABEL = "No file selected"

def select_file(label: QPushButton):
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select a File",
        "",
        "All Files (*.*);;Text Files (*.txt);;Image Files (*.png *.jpg *.jpeg)"
    )

    if file_path:
        label.setText(f"{file_path}")
    else:
        label.setText(FILE_SELECTOR_NULL_LABEL)