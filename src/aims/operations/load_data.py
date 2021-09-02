from PyQt5.QtWidgets import QApplication
from aims.operations.load_data_operation import LoadDataOperation


def load_data(model, aims_status_dialog):
    operation = LoadDataOperation(model)
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    aims_status_dialog.progress_dialog.close()
