import os

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

from aims.operations.kml_to_geojson import make_geojson


class RoutesComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.widget = None
        self.aims_status_dialog = None
        self.hint_function = hint_function
        self.parent = None

    def set_hint(self):
        self.hint_function("")
        if self.widget.inputFolderText.text() == "":
            self.hint_function("Choose the input folder where the kml files are")
            return

        if self.widget.outputFolderText.text() == "":
            self.hint_function("Choose the output folder")
            return

        if not self.widget.afterProcessWidget.isVisible():
            self.hint_function('Press the button "Create GeoJson"')
            return

        self.hint_function('Copy the output files to the device')

    def load_screen(self, aims_status_dialog, parent):
        self.aims_status_dialog = aims_status_dialog
        self.widget.afterProcessWidget.setVisible(False)
        self.widget.inputFolderButton.clicked.connect(self.openInputFolder)
        self.widget.outputFolderButton.clicked.connect(self.openOutputFolder)
        self.widget.processButton.clicked.connect(self.process)
        self.widget.openFolderButton.clicked.connect(self.open_folder)
        self.parent = parent
        self.set_hint()

    def process(self):
        input_folder = self.widget.inputFolderText.text()
        output_folder = f"{self.widget.outputFolderText.text()}/geojson"
        make_geojson(input_folder, output_folder)
        self.widget.afterProcessWidget.setVisible(True)
        self.widget.outputFolderLabel.setText(f"      {output_folder}")
        self.set_hint()

    def openInputFolder(self):
        file = str(QFileDialog.getExistingDirectory(self.parent, "Select Directory"))
        if file:
            self.widget.inputFolderText.setText(file)
        self.set_hint()

    def openOutputFolder(self):
        file = str(QFileDialog.getExistingDirectory(self.parent, "Select Directory"))
        if file:
            self.widget.outputFolderText.setText(file)
        self.set_hint()

    def open_folder(self):
        os.startfile(self.widget.outputFolderLabel.text().strip())



