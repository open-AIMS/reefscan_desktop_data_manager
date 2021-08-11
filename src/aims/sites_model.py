import os
from aims.json_utils import read_json_file
from aims.json_utils import write_json_file
from aims.widgets.aims_abstract_table_model import AimsAbstractTableModel


class SitesModel(AimsAbstractTableModel):

    columns = ["name", "latitude", "longitude", "folder"]
    editable = [True,True,True, False ]

    def save_data(self, row):
        site = self.data_array[row]
        self.save_site(site)

    def save_site(self, site):
        site_to_save = site.copy()
        site_to_save.pop('uuid')
        folder = site_to_save.pop('folder')
        write_json_file(folder, 'site.json', site_to_save)

    def read_data(self, datafolder):
        self.datafolder = datafolder
        self.data_array=[]
        sitesFolder = f'{self.datafolder}/sites'
        siteFolders = os.listdir(sitesFolder)
        for siteFolder in siteFolders:
            fullPath = f'{sitesFolder}/{siteFolder}'
            if os.path.isdir(fullPath):
                siteFile = f'{fullPath}/site.json'
                site = read_json_file(siteFile)
                site["folder"] = fullPath
                site["uuid"] = siteFolder
                self.data_array.append(site)
