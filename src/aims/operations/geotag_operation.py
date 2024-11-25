import logging
import traceback

from PyQt5.QtWidgets import QApplication
from reefscanner.basic_model.survey import Survey

from aims.operations.abstract_operation import AbstractOperation
from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.state import state

from aims.tools.geocode import Geocode

logger = logging.getLogger("")

def geocode_folder(gpx_file, image_folder, aims_status_dialog: AimsStatusDialog, camera_diff_seconds=0, timezone="Z"):
    operation = GeotagOperation(gpx_file, image_folder, camera_diff_seconds, timezone)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()

    logger.info("Close the status dialog")
    aims_status_dialog.close()
    if not operation.success:
        raise Exception(f"error geocoding {image_folder}. {operation.message}")

def geocode_folders(survey_infos, gpx_file, aims_status_dialog: AimsStatusDialog, camera_diff_seconds=0, timezone="Z"):
    for survey_info in survey_infos:
        survey: Survey = state.model.surveys_data[survey_info["survey_id"]]
        print(f"geotag {survey.folder}")
        geocode_folder(gpx_file, survey.folder, aims_status_dialog, camera_diff_seconds, timezone)



class GeotagOperation(AbstractOperation):


    def __init__(self, gpx_file, image_folder, camera_diff_seconds=0, timezone="Z"):
        super().__init__()
        self.gpx_file = gpx_file
        self.image_folder = image_folder
        self.camera_diff_seconds = camera_diff_seconds
        self.timezone = timezone
        self.geocode = Geocode(self.progress_queue)
        self.message = ""

    def _run(self):
        self.finished = False
        self.success = False
        logger.info("start subsample")
        try:
            self.geocode.geocode(self.gpx_file, self.image_folder, self.camera_diff_seconds, self.timezone)
            self.success = True
        except Exception as e:
            logger.error("ERROR ERROR")
            traceback.print_exc()
            self.message = str(e)
            logger.info(self.message)
            self.success = False

        logger.info("finish load data")
        self.finished = True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            self.geocode.canceled = True



