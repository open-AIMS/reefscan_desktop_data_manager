import typing

from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class CheckTreeitem(QStandardItem):

    def __init__(self, label, checkable):
        super().__init__(label)
        super().setCheckable(checkable)

    def cascade_check(self) -> None:
        print("cascade check state")
        state = self.checkState()
        for i in range(self.rowCount()):
            child_item = self.child(i)
            child_item.setCheckState(state)


