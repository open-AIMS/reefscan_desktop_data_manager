from PyQt5.QtWidgets import QApplication

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.load_data_operation import LoadDataOperation


def load_data(model, aims_status_dialog: AimsStatusDialog):
    operation = LoadDataOperation(model)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    aims_status_dialog.close()

