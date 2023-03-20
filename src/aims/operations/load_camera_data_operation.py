import logging
import sys
import traceback

from reefscanner.basic_model.basic_model import BasicModel

from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger(__name__)


class LoadCameraDataOperation(AbstractOperation):

    def __init__(self, model: BasicModel):
        super().__init__()
        self.model = model
        self.finished=False
        self.success=False
        self.message = ""

    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start load data")
        try:
            self.model.load_camera_data(self.progress_queue)
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

