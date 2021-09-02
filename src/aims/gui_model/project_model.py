from reefscanner.basic_model.reader_writer import save_site
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class ProjectsModel(AimsAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.columns = ["name"]
        self.editable = [False]

    def save_data(self, row):
        pass

