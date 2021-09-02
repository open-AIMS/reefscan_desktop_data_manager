import logging

from aims.gui_model.model import GuiModel
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger(__name__)


class LoadDataOperation(AbstractOperation):

    def __init__(self, model: GuiModel):
        super().__init__()
        self.model = model

    def _run(self):
        logger.info("start load data")
        self.model.read_from_files(self.progress_queue)
        logger.info("finish load data")
        return None

    def cancel(self):
        pass

