import logging
import sys
import traceback

from reefscanner.basic_model.basic_model import BasicModel

from aims.messages import messages
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger("")


class LoadDataOperation(AbstractOperation):

    def __init__(self, model: BasicModel, camera_connected):
        super().__init__()
        self.model = model
        self.finished=False
        self.success=False
        self.message = ""
        self.camera_connected = camera_connected

    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start load data")
        try:
            self.model.read_from_files(self.progress_queue, self.camera_connected#,
                                       #message=messages.load_local_data_message(),
                                       #error_message=messages.load_local_data_error_message()
                                       )
            self.success = True
        except Exception as e:
            logger.error("ERROR ERROR: load_data_operation from real_src")
            traceback.print_exc()
            self.message = str(e)
            print(self.message)
            logger.error(self.message)
            self.success = False

        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            sys.exit()

