
import os

from reefscanner.basic_model.reader_writer import save_survey
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class SurveysModel(AimsAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.data_dict = {}


    def save_data(self, row):
        survey = self.data_array[row]
        save_survey(survey)

    def set_hardware_data_folder(self, data_folder):
        if os.path.isdir(data_folder):
            self.hardware_data_folder = data_folder
            self.read_from_files()

    def clear_data(self):
        self.data_array = []

