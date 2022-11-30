import win32file
from PyQt5 import QtCore


class NoNetworkDrivesFilter (QtCore.QSortFilterProxyModel): #Custom Proxy Model
    def __init__(self, parent=None):
        super(NoNetworkDrivesFilter,self).__init__(parent)

    def filterAcceptsRow(self, row, parent): #returns true if the given row should be included in the model

        # sourceModel()->data(index0).toString().contains("C:")
        model = self.sourceModel()
        index = model.index(row, 0, parent)
        print (str(model.data(index)))
        file_info = model.fileInfo(index)
        if not file_info.isDir():
            return False

        if not file_info.isRoot():
            return True

        drive_type = win32file.GetDriveType(file_info.canonicalFilePath())

        return drive_type == win32file.DRIVE_FIXED
