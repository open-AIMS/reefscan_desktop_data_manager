import os

from PyQt5.QtWidgets import QTableView, QAbstractItemView
from PyQt5 import QtWidgets
from reefscanner.basic_model.reader_writer import save_site

from aims.widgets.combo_box_delegate import ComboBoxDelegate


class SurveysTable(object):

    def __init__(self, tblSurveys: QTableView, surveys_model, gui_model=None, make_site_column=3, show_folder_column=11):
        super().__init__()
        self.surveys_model = surveys_model
        self.gui_model = gui_model
        self.make_site_column = make_site_column
        self.show_folder_column = show_folder_column
        tblSurveys.setModel(surveys_model)

        tblSurveys.setEditTriggers(
            QAbstractItemView.SelectedClicked | QAbstractItemView.AnyKeyPressed | QAbstractItemView.DoubleClicked)

        self.projectsComboBox = ComboBoxDelegate(surveys_model.projects_lookup)
        tblSurveys.setItemDelegateForColumn(1, self.projectsComboBox)
        self.sitesComboBox = ComboBoxDelegate(surveys_model.sites_lookup)
        self.sitesComboBox.setChoices(surveys_model.sites_lookup)
        self.projectsComboBox.setChoices(surveys_model.projects_lookup)

        tblSurveys.setItemDelegateForColumn(2, self.sitesComboBox)
        tblSurveys.resizeColumnsToContents()

        tblSurveys.clicked.connect(self.table_clicked)

    def table_clicked(self, index):
        if index.column() == self.show_folder_column:
            path = self.surveys_model.data_array[index.row()]["folder"]
            os.startfile(path)
        if index.column() == self.make_site_column:
            self.make_site(index)

    def make_site(self, index):
        input_box = QtWidgets.QInputDialog()
        input_box.setLabelText("Site Name")
        result = input_box.exec_()
        if result == QtWidgets.QDialog.Accepted:
            site_name = input_box.textValue()
            self.surveys_model.new_site_for_survey(index.row(), site_name)
            self.sitesComboBox.setChoices(self.surveys_model.sites_lookup)
            if self.gui_model is not None:
                self.gui_model.add_new_sites(self.surveys_model.new_sites)
                self.surveys_model.new_sites = []

                self.surveys_model.save_data(index.row())




