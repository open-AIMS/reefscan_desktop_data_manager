import logging
from time import process_time

from PyQt5.QtWidgets import QApplication
from reefscanner.basic_model.model_utils import print_time
from reefscanner.basic_model.survey import Survey

from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.operations.geotag_operation import GeotagOperation
from aims2.operations2.load_archive_data_operation import LoadArchiveDataOperation
from aims2.operations2.load_camera_data_operation import LoadCameraDataOperation
from aims2.operations2.load_data_operation import LoadDataOperation
from aims.operations.reefcloud_sub_sample_operation import ReefcloudSubSampleOperation
from aims.operations.reefcloud_upload_operation import ReefcloudUploadOperation

logger = logging.getLogger("load_data")


def load_data(model, camera_connected, aims_status_dialog: AimsStatusDialog):
    start = process_time()
    logger.info (f"start load data method {process_time()}")
    operation = LoadDataOperation(model, camera_connected)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    print_time("load data setup", start, logger)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    print_time("load data start", start, logger)
    while not result.ready():
        QApplication.processEvents()
    print_time("load data finish", start, logger)

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    print (operation.message)
    return operation.success, operation.message


def reefcloud_subsample(image_dirs, sample_dir, aims_status_dialog: AimsStatusDialog):
    logger.info(f"start sub_sample {process_time()}")
    operation = ReefcloudSubSampleOperation(image_dirs, sample_dir)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    return operation.success, operation.selected_photo_infos, operation.message


def reefcloud_upload_survey(survey: Survey, survey_id, survey_folder, subsampled_image_folder, aims_status_dialog: AimsStatusDialog):
    operation = ReefcloudUploadOperation(survey, survey_id, survey_folder, subsampled_image_folder)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    return operation.success, operation.message

def load_camera_data(model, aims_status_dialog: AimsStatusDialog):
    operation = LoadCameraDataOperation(model)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    print (operation.message)
    return operation.success, operation.message, operation.space_available


def load_archive_data(model, aims_status_dialog: AimsStatusDialog):

    operation = LoadArchiveDataOperation(model)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    print (operation.message)
    return operation.success, operation.message
