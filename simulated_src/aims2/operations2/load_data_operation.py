import logging
import sys
import traceback

from reefscanner.basic_model.basic_model import BasicModel
from reefscanner.basic_model.survey import Survey

from aims.messages import messages
from aims.state import state
from aims.operations.abstract_operation import AbstractOperation
from aims2.operations2.count_to_three import count_to_three

logger = logging.getLogger("")


class LoadDataOperation(AbstractOperation):

    def __init__(self, model: BasicModel, camera_connected):
        super().__init__()
        self.model = model
        self.finished=False
        self.success=False
        self.message = ""
        self.camera_connected = camera_connected
        self.model.data_folder = f'{state.meipass}fake_data/local'

    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start load data")
        try:
            self.model.read_from_files(self.progress_queue, self.camera_connected,
                                       message=messages.load_local_data_message(),
                                       error_message=messages.load_local_data_error_message()
                                       )
            count_to_three(progress_queue=self.progress_queue, message=messages.load_local_data_message())

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


