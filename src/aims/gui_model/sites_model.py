from reefscanner.basic_model.reader_writer import save_site
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class SitesModel(AimsAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.columns = ["name", "latitude", "longitude", "folder"]
        self.editable = [True,True,True, False ]

    def save_data(self, row):
        site = self.data_array[row]
        save_site(site, self.data_array)

