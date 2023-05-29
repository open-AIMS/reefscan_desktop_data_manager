import logging
import threading

from aims.operations.abstract_operation import AbstractOperation

from photoenhancer.photoenhance import photoenhance

logger = logging.getLogger("")

class EnhancePhotoOperation(AbstractOperation):
    target: str = ""
    load: float = 0.01
    suffix: str = ""

    def __init__(self, target, load, suffix, output_folder='enhanced'):
        super().__init__()
        self.target = target
        self.output_folder = output_folder
        self.load = load
        self.suffix = suffix

    def _run(self):
        use_suffix = 'True' if self.suffix is not None else 'False'
        t = threading.Thread(target=lambda: photoenhance(target=self.target, 
                                                         output_folder=self.output_folder, 
                                                         load=self.load, 
                                                         use_suffix=use_suffix, 
                                                         suffix=self.suffix))
        t.start()
        t.join()
        # return self.sync.sync(survey_infos=self.surveys)
