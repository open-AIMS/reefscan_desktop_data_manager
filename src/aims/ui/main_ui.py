from PyQt5.QtWidgets import QMainWindow, QWidget, QFileSystemModel
from PyQt5 import QtWidgets, uic
from aims import state
import sys
import logging
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent, QStandardPaths

from aims.gui_model.tree_model import make_tree_model
from aims.operations.aims_status_dialog import AimsStatusDialog

workflow_button_border = ";border: 5px solid red;"
def add_button_border(button):
    style = button.styleSheet()
    style = style + workflow_button_border
    button.setStyleSheet(style)

def remove_button_border(button):
    style = button.styleSheet()
    style = style.replace(workflow_button_border, "")
    button.setStyleSheet(style)

class MainUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.start_ui = f'{state.meipass}resources/main.ui'
        self.ui = uic.loadUi(self.start_ui)

        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)

        self.workflow_widget = None
        self.connect_widget = None

        self.setup_workflow()
        self.setup_status()

        self.load_start_screen()
        self.aims_status_dialog = AimsStatusDialog(self.ui)


    def setup_status(self):
        status_widget_file = f'{state.meipass}resources/status-bar.ui'
        status_widget: QWidget = uic.loadUi(status_widget_file)
        self.ui.statusFrame.layout().addWidget(status_widget)

    def highlight_button(self, button):
        remove_button_border(self.workflow_widget.connectButton)
        remove_button_border(self.workflow_widget.downloadButton)
        remove_button_border(self.workflow_widget.backupButton)
        remove_button_border(self.workflow_widget.exploreButton)
        remove_button_border(self.workflow_widget.checkButton)

        add_button_border(button)



    def setup_workflow(self):
        workflow_widget_file = f'{state.meipass}resources/workflow-bar.ui'
        self.workflow_widget: QWidget = uic.loadUi(workflow_widget_file)
        self.ui.workflowFrame.layout().addWidget(self.workflow_widget)
        self.workflow_widget.connectButton.clicked.connect(self.load_connect_screen)
        self.workflow_widget.downloadButton.clicked.connect(self.load_download_screen)
        self.workflow_widget.downloadButton.setEnabled(False)
        self.workflow_widget.exploreButton.clicked.connect(self.load_explore_screen)
        self.workflow_widget.checkButton.clicked.connect(self.load_check_screen)
        self.workflow_widget.backupButton.clicked.connect(self.load_backup_screen)

    def load_start_screen(self):
        self.load_main_frame(f'{state.meipass}resources/start.ui')

    def load_download_screen(self):
        download_widget = self.load_main_frame(f'{state.meipass}resources/download.ui')
        self.highlight_button(self.workflow_widget.downloadButton)
        model = QFileSystemModel()
        # model.setRootPath(QStandardPaths.displayName(QStandardPaths.DesktopLocation))
        model.setRootPath("c:\\")
        destination_tree = download_widget.destinationTree
        destination_tree.setModel(model)
        destination_tree.setRootIndex(model.index("c:\\"))
        for i in range(1, destination_tree.model().columnCount()):
            destination_tree.header().hideSection(i)
        camera_tree = download_widget.cameraTree
        camera_model = make_tree_model(include_local=False)
        camera_tree.setModel(camera_model)

    def load_explore_screen(self):
        w = self.load_main_frame(f'{state.meipass}resources/not-implemented.ui')
        self.highlight_button(self.workflow_widget.exploreButton)

    def load_check_screen(self):
        w = self.load_main_frame(f'{state.meipass}resources/not-implemented.ui')
        self.highlight_button(self.workflow_widget.checkButton)

    def load_backup_screen(self):
        w = self.load_main_frame(f'{state.meipass}resources/not-implemented.ui')
        self.highlight_button(self.workflow_widget.backupButton)

    def load_connect_screen(self):
        self.connect_widget = self.load_main_frame(f'{state.meipass}resources/connect.ui')
        html = self.connect_widget.textBrowser.toHtml()
        html = html.replace("XXX_DIR_XXX", state.meipass2)
        self.connect_widget.textBrowser.setHtml(html)
        self.connect_widget.btnConnect.clicked.connect(self.connect)
        self.highlight_button(self.workflow_widget.connectButton)


    def load_main_frame(self, ui_file):
        self.clearLayout(self.ui.mainFrame.layout())
        widget: QWidget = uic.loadUi(ui_file)
        self.ui.mainFrame.layout().addWidget(widget)
        return widget

    def connect(self):
        state.load_camera_data_model(aims_status_dialog=self.aims_status_dialog)
        if state.model.data_loaded:
            self.connect_widget.lblMessage.setText("Connected Successfully")
            self.workflow_widget.downloadButton.setEnabled(True)
            self.load_download_screen()
        else:
            self.connect_widget.lblMessage.setText(state.model.message)

    def show(self):
        self.ui.show()

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())


