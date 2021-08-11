from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtWidgets, uic

from aims.onbard_sync_model import OnboardSyncModel
from aims.widgets.combo_box_delegate import ComboBoxDelegate


class OnboardSyncDlg(QDialog):

    model: OnboardSyncModel

    def __init__(self, ui, model):
        super().__init__()
        self.model = model
        self.ui = uic.loadUi(ui, baseinstance=self)
        self.ui.tableView.setModel(self.model)
        self.projectsComboBox = ComboBoxDelegate(self.model.projects_lookup)
        self.ui.tableView.setItemDelegateForColumn(1, self.projectsComboBox)
        self.sitesComboBox = ComboBoxDelegate(self.model.sites_lookup)
        self.ui.tableView.setItemDelegateForColumn(2, self.sitesComboBox)

        self.ui.setWindowState(self.ui.windowState() | Qt.WindowMaximized)
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.setColumnWidth(1, 120)
        self.ui.tableView.setColumnWidth(2, 200)
        self.ui.tableView.clicked.connect(self.table_clicked)

    def table_clicked(self, index):
        if index.column() == 3:
            self.make_site(index)

    def make_site(self, index):
        print("make site")
        input_box = QtWidgets.QInputDialog()
        input_box.setLabelText("Site Name")
        result = input_box.exec_()
        if result == QDialog.Accepted:
            site_name = input_box.textValue()
            self.model.new_site_for_survey(index.row(), site_name)
            self.sitesComboBox.setChoices(self.model.sites_lookup)



