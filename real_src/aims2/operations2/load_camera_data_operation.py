import logging
import sys
import traceback
import unicodedata

import smbclient
from reefscanner.basic_model.basic_model import BasicModel

from aims.messages import messages
from aims.operations.abstract_operation import AbstractOperation
from aims.state import state

logger = logging.getLogger("")

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


class LoadCameraDataOperation(AbstractOperation):

    def __init__(self, model: BasicModel):
        super().__init__()
        self.model = model
        self.finished=False
        self.success=False
        self.message = ""
        self.space_available = None

    def _run(self):
        self.finished=False
        self.success = False
        logger.info("start load data")
        try:
            self.model.load_camera_data(self.progress_queue,
                                        message=messages.load_camera_data_message(),
                                        error_message=messages.load_camera_data_error_message()
                                        )
            self.progress_queue.reset()
            self.progress_queue.set_progress_label("Setting up ...")
            state.reefscan_id = remove_control_characters(state.read_reefscan_id())
            self.space_available = smbclient._os.stat_volume(state.model.camera_data_folder)

            self.success = True
        except Exception as e:
            logger.error("ERROR ERROR")
            traceback.print_exc()
            self.message = str(e)
            logger.info(self.message)
            self.success = False

        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            sys.exit()

