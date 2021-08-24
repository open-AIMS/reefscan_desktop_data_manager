from reefscanner.basic_model.reader_writer import save_site
from aims.gui_model.aims_abstract_table_model import AimsAbstractTableModel


class SitesModel(AimsAbstractTableModel):

    columns = ["name", "latitude", "longitude", "folder"]
    editable = [True,True,True, False ]

    def save_data(self, row):
        site = self.data_array[row]
        save_site(site, self.data_array)

