import logging
import os


from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QEvent

from PyQt5.QtWidgets import QCheckBox, QMessageBox, QMainWindow, QLineEdit

from aims import state
from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.ui.ui_utils import unHighlight, highlight

logger = logging.getLogger(__name__)


class ConfigUi(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = f'{state.meipass}resources/config.ui'
        self.ui = uic.loadUi(ui_file)

        self.lbl_next_step = self.ui.lblNextStep
        self.ed_local: QLineEdit = self.ui.edLocal
        self.ed_backup: QLineEdit = self.ui.edBackup
        self.ed_vessel: QLineEdit = self.ui.ed_vessel
        self.ed_observer: QLineEdit = self.ui.ed_observer
        self.ed_operator: QLineEdit = self.ui.ed_operator

        cb_slow_network: QCheckBox = self.ui.cbSlowNetwork
        cb_slow_network.setChecked(state.config.slow_network)

        self.ui.cbCamera.setChecked(state.config.camera_connected)

        self.ui.edLocal.setText(state.config.data_folder)
        self.ui.edBackup.setText(state.config.backup_data_folder)

        self.ui.btnLocal.clicked.connect(self.local_clicked)
        self.ui.btnBackup.clicked.connect(self.backup_clicked)

        self.ui.btn_next.clicked.connect(self.finished)
        self.aims_status_dialog = AimsStatusDialog(self.ui)

        self.ui.ed_vessel.setText(state.config.default_vessel)
        self.ui.ed_observer.setText(state.config.default_observer)
        self.ui.ed_operator.setText(state.config.default_operator)
        self.ui.ed_camera_folder.setText(state.config.hardware_data_folder)
        self.ui.wid_main.installEventFilter(self)

        self.ed_local.editingFinished.connect(self.update_next_step)
        self.ed_backup.editingFinished.connect(self.update_next_step)
        self.ed_operator.editingFinished.connect(self.update_next_step)
        self.ed_observer.editingFinished.connect(self.update_next_step)
        self.ed_vessel.editingFinished.connect(self.update_next_step)

        self.ed_local.returnPressed.connect(self.next_tab)
        self.ed_backup.returnPressed.connect(self.next_tab)
        self.ed_operator.returnPressed.connect(self.next_tab)
        self.ed_observer.returnPressed.connect(self.next_tab)
        self.ed_vessel.returnPressed.connect(self.next_tab)

        self.update_next_step()

    def eventFilter(self, source, event):
        # print(event.type())
        if event.type() == QEvent.Leave:
            self.save_config()

        return super(ConfigUi, self).eventFilter(source, event)

    def reset_next_step(self):
        self.ui.btn_next.setEnabled(False)
        unHighlight(self.ui.btnLocal)
        unHighlight(self.ui.btnBackup)

        unHighlight(self.ed_operator)
        unHighlight(self.ed_observer)
        unHighlight(self.ed_vessel)

    def next_tab(self):
        self.ui.focusNextChild()

    def update_next_step(self):
        self.reset_next_step()
        if self.ed_local.text() == "":
            self.lbl_next_step.setText("Enter the local folder where you will store your data")
            highlight(self.ui.btnLocal)
            return

        if not os.path.isdir(self.ed_local.text()):
            self.lbl_next_step.setText("Data folder is invalid. Enter the local folder where you will store your data")
            highlight(self.ui.btnLocal)
            return

        if self.ed_backup.text() == "":
            self.lbl_next_step.setText("Enter the folder where you will store a backup of your data.")
            highlight(self.ui.btnBackup)
            return

        if not os.path.isdir(self.ed_backup.text()):
            self.lbl_next_step.setText("Backup folder is invalid. Enter the folder where you will store a backup of your data.")
            highlight(self.ui.btnBackup)
            return

        if self.ed_operator.text() == "":
            self.lbl_next_step.setText("Enter a default operator. The person who will usually be operating the equipment.")
            highlight(self.ed_operator)
            return

        if self.ed_observer.text() == "":
            self.lbl_next_step.setText("Enter a default observer. The person who will usually be observing the operation.")
            highlight(self.ed_observer)
            return

        if self.ed_vessel.text() == "":
            self.lbl_next_step.setText("Enter a default vessel. The vessel which will usually be used.")
            highlight(self.ed_vessel)
            return

        self.ui.btn_next.setEnabled(True)
        highlight(self.ui.btn_next)
        self.lbl_next_step.setText("Hit the next button to continue")


    def show(self):
        self.ui.show()

    def finished(self, page_id):
        logger.info("finished")
        self.save_config()

        state.load_data_model(aims_status_dialog=self.aims_status_dialog)


        if state.model.data_loaded:
            state.surveys_tree.show()
            self.ui.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(state.model.message)
            msg.setWindowTitle("Error")
            msg.exec_()

        logger.info("Really finished")

    def save_config(self):
        state.config.data_folder = self.ui.edLocal.text()
        state.config.backup_data_folder = self.ui.edBackup.text()
        state.config.slow_network = self.ui.cbSlowNetwork.isChecked()
        state.config.camera_connected = self.ui.cbCamera.isChecked()
        state.config.default_vessel = self.ui.ed_vessel.text()
        state.config.default_observer = self.ui.ed_observer.text()
        state.config.default_operator = self.ui.ed_operator.text()
        state.config.hardware_data_folder = self.ui.ed_camera_folder.text()
        state.config.save_config_file()

    def local_clicked(self):
        self.choose_file(self.ui.edLocal)

    def backup_clicked(self):
        self.choose_file(self.ui.edBackup)

    def server_clicked(self):
        self.choose_file(self.ui.edServer)

    def choose_file(self, edit_box):
        filedialog = QtWidgets.QFileDialog(self.ui)
        filedialog.setFileMode(QtWidgets.QFileDialog.Directory)
        filedialog.setDirectory(edit_box.text())
        selected = filedialog.exec()
        if selected:
            filename = filedialog.selectedFiles()[0]
            edit_box.setText(filename)

        self.update_next_step()
