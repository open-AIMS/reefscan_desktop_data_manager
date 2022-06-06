import logging
import sys

from aims.gui_model.model import GuiModel
from aims.operations.abstract_operation import AbstractOperation

logger = logging.getLogger(__name__)


class LoadDataOperation(AbstractOperation):

    def __init__(self, model: GuiModel):
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
            self.model.read_from_files(self.progress_queue)
            self.success = True
        except Exception as e:
            logger.info("ERROR ERROR")
            logger.info (str(e))
            self.message = str(e)
            self.success=False
        logger.info("finish load data")
        self.finished=True

        return None

    def cancel(self):
        if not self.finished:
            logger.info("I will cancel")
            sys.exit()

