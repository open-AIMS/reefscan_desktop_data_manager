from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QStandardItem, QColor


class CheckTreeitem(QStandardItem):

    def __init__(self, label, checkable, grey=False):
        super().__init__(label)
        super().setCheckable(checkable)
        if grey:
            super().setData(QVariant(QColor(Qt.gray)), Qt.ForegroundRole)

    def cascade_check(self) -> None:
        # logger.info("cascade check state")
        state = self.checkState()
        for i in range(self.rowCount()):
            child_item = self.child(i)
            child_item.setCheckState(state)


