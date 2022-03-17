import logging
import sys

from aims.gui_model.model import GuiModel
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger(__name__)


class LoadDataOperation(AbstractOperation):

    def __init__(self, model: GuiModel):
        super().__init__()
        self.model = model
        finished=False

    def _run(self):
        finished=False
        logger.info("start load data")
        self.model.read_from_files(self.progress_queue)
        logger.info("finish load data")
        finished=True
        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            sys.exit()

