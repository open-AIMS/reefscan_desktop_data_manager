import os
from aims.utils import readJsonFile
from aims.utils import writeJsonFile
from aims.widgets.aims_abstract_table_model import AimsAbstractTableModel


class SitesModel(AimsAbstractTableModel):

    columns = ["name", "latitude", "longitude", "folder"]
    editable = [True,True,True, False ]

    def saveData(self, row):
        site = self.data[row].copy()
        uuid = site.pop('uuid')
        folder = site.pop('folder')

        writeJsonFile(f'{folder}/site.json', site)


    def readData(self, datafolder):
        self.datafolder = datafolder
        self.data=[]
        sitesFolder = f'{self.datafolder}/sites'
        siteFolders = os.listdir(sitesFolder)
        for siteFolder in siteFolders:
            fullPath = f'{sitesFolder}/{siteFolder}'
            if os.path.isdir(fullPath):
                siteFile = f'{fullPath}/site.json'
                site = readJsonFile(siteFile)
                site["folder"] = fullPath
                site["uuid"] = siteFolder
                self.data.append(site)
        print(self.data)