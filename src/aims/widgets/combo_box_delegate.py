from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import QTimer

class ComboBoxDelegate(QtWidgets.QItemDelegate):
    def __init__(self, choices, parent=None):
        super().__init__(parent)
        self.choices = choices
        self.valueIndex =list(self.choices.keys())

    def setChoices(self, choices):
        self.choices = choices


    def createEditor(self, parent, option, index):
        self.editor = QtWidgets.QComboBox(parent)
        for key, value in self.choices.items():
            self.editor.addItem(value, key)
        QTimer.singleShot(0, self.showPopup)
        return self.editor

    @QtCore.pyqtSlot()
    def showPopup(self):
        self.editor.showPopup()

    def paint(self, painter, option, index):
        value = index.data(QtCore.Qt.DisplayRole)
        style = QtWidgets.QApplication.style()
        opt = QtWidgets.QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter)
        style.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt, painter)
        QtWidgets.QItemDelegate.paint(self, painter, option, index)

    def setEditorData(self, editor, index):
        try:
            value = index.data(QtCore.Qt.EditRole)
            num = self.valueIndex.index(value)
            editor.setCurrentIndex(num)
        except Exception as e:
            logger.info(e)


    def setModelData(self, editor, model, index):
        value = editor.currentData()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
