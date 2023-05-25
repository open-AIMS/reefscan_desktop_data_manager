import logging
import threading

from aims.operations.abstract_operation import AbstractOperation

from photoenhancer.photoenhance import photoenhance

logger = logging.getLogger("")

class EnhancePhotoOperation(AbstractOperation):
    target: str = ""
    load: float = 0.01
    suffix: str = ""

    def __init__(self, target, load, suffix):
        super().__init__()
        self.target = target
        self.load = load
        self.suffix = suffix

    def _run(self):
        
        t = threading.Thread(target=lambda: photoenhance(target=self.target, load=self.load, suffix=self.suffix))
        t.start()
        t.join()
        # return self.sync.sync(survey_infos=self.surveys)
