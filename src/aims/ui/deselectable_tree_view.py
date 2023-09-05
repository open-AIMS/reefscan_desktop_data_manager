from PyQt5.QtWidgets import QTreeView

import logging
logger = logging.getLogger("")
class DeselectableTreeView(QTreeView):
    def mousePressEvent(self, event):
        # self.clearSelection()
        QTreeView.mousePressEvent(self, event)
