import logging

from reefscanner.basic_model.reader_writer import read_survey_data

from aims.gui_model.hardware_sync_model import HardwareSyncModel
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger(__name__)


class LoadHardwareSyncDataOperation(AbstractOperation):

    def __init__(self, model: HardwareSyncModel):
        super().__init__()
        self.model = model

    def _run(self):
        logger.info("start load data")
        read_survey_data(self.model.data_folder, self.model.trip, self.model.default_project,
                         self.model.default_operator, self.model.data_array, self.progress_queue)

        logger.info("finish load data")
        return None

    def cancel(self):
        pass

