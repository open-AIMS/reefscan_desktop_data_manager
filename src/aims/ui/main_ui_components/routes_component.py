import os

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

from aims import utils
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
            self.hint_function(self.tr("Choose the input folder where the kml files are"))
            return

        if self.widget.outputFolderText.text() == "":
            self.hint_function(self.tr("Choose the output folder"))
            return

        if not self.widget.afterProcessWidget.isVisible():
            self.hint_function(self.tr('Press the button "Create GeoJson"'))
            return

        self.hint_function(self.tr('Copy the output files to the device'))

    def load_screen(self, aims_status_dialog, parent):
        self.aims_status_dialog = aims_status_dialog
        self.widget.afterProcessWidget.setVisible(False)
        self.widget.inputFolderButton.clicked.connect(self.openInputFolder)
        self.widget.outputFolderButton.clicked.connect(self.openOutputFolder)
        self.widget.processButton.clicked.connect(self.process)
        self.widget.openFolderButton.clicked.connect(self.open_folder)
        self.parent = parent

        head = self.tr("You can create routes or paths to follow. Then upload these to tablet.")

        s1 = self.tr("Use google earth or similar to create the routes in one or more kml files.")
        s2 = self.tr("Place the kml files in a single folder")
        s3 = self.tr("Use this form to create geojson files")
        s4 = self.tr("Connect your computer to the tablet using a USB cable")
        s5 = self.tr("Copy the GeoJson files to the tablet")
        html = self.widget.textBrowser.toHtml()
        html = html.replace("__head__", head)
        html = html.replace("__s1__", s1)
        html = html.replace("__s2__", s2)
        html = html.replace("__s3__", s3)
        html = html.replace("__s4__", s4)
        html = html.replace("__s5__", s5)
        self.widget.textBrowser.setHtml(html)

        self.set_hint()

    def process(self):
        input_folder = self.widget.inputFolderText.text()
        output_folder = self.widget.outputFolderText.text()
        geojson_folder = f"{output_folder}/geojson"
        gpx_folder = f"{output_folder}/gpx"

        make_geojson(input_folder, geojson_folder, gpx_folder)
        self.widget.afterProcessWidget.setVisible(True)
        self.widget.outputFolderLabel.setText(f"      {geojson_folder}")
        self.widget.gpx_folder_label.setText(f"And copy the the files from {gpx_folder} to the gps")
        self.set_hint()

    def openInputFolder(self):
        file = str(QFileDialog.getExistingDirectory(self.parent, self.tr("Select Directory")))
        if file:
            self.widget.inputFolderText.setText(file)
        self.set_hint()

    def openOutputFolder(self):
        file = str(QFileDialog.getExistingDirectory(self.parent, self.tr("Select Directory")))
        if file:
            self.widget.outputFolderText.setText(file)
        self.set_hint()

    def open_folder(self):
        utils.open_file(self.widget.outputFolderLabel.text().strip())



