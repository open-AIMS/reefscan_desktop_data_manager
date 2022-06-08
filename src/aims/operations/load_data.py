import logging

from PyQt5.QtWidgets import QApplication

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.load_data_operation import LoadDataOperation

logger = logging.getLogger(__name__)


def load_data(model, camera_connected, aims_status_dialog: AimsStatusDialog):
    operation = LoadDataOperation(model, camera_connected)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    print (operation.message)
    return operation.success, operation.message

