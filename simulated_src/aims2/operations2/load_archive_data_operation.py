import logging
import sys
import traceback

from reefscanner.basic_model.basic_model import BasicModel

from aims.messages import messages
from aims.state import state
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger("")


class LoadArchiveDataOperation(AbstractOperation):

    def __init__(self, model: BasicModel):
        super().__init__()
        self.model = model
        self.finished=False
        self.success=False
        self.message = ""
        self.model.camera_data_folder = f'{state.meipass}fake_data/camera'
        self.model.camera_samba = False

    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start load data")
        try:
            self.model.load_camera_archive_data(self.progress_queue,
                                                message=messages.load_camera_data_message(),
                                                error_message=messages.load_camera_data_error_message())
            self.success = True
        except Exception as e:
            logger.error("ERROR ERROR")
            traceback.print_exc()
            self.message = str(e)
            print(self.message)
            self.success = False

        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            sys.exit()

