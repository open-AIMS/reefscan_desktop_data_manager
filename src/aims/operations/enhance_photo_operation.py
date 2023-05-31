import logging
import threading

from aims.operations.abstract_operation import AbstractOperation

from photoenhancer.photoenhance import photoenhance
from photoenhancer.photoenhance import BatchMonitor

logger = logging.getLogger("")

class EnhancePhotoOperation(AbstractOperation):
    target: str = ""
    load: float = 0.01
    suffix: str = ""
    msg_func = lambda msg: None
    teststring = ""

    def __init__(self, target, load, suffix, output_folder='enhanced'):
        super().__init__()
        self.target = target
        self.output_folder = output_folder
        self.load = load
        self.suffix = suffix
        self.batch_monitor = BatchMonitor()

    def _run(self):
        logger.info("EnhancePhotoOperation run")

        def retrieve_current_progress(completed, total):
            self.set_progress_max(total)
            self.set_progress_value(completed)
            self.set_progress_label(f'Enhancing: {completed} / {total} done')

        self.batch_monitor.set_callback_on_tick(retrieve_current_progress)

        t = threading.Thread(target=self.enhance_photos)
        t.start()
        t.join()

    def cancel(self):
        logger.info("enhance photo operation says cancel")
        self.batch_monitor.set_cancelled()
        if self.msg_func is not None:
            if not self.batch_monitor.finished:
                self.msg_func("Stopping enhance operation...") 
                self.msg_func("Waiting for the enhancer to finish shutting down. This will take a few seconds.")
        # while not self.batch_monitor.finished:
        #     self.set_progress_label('Cancelled. Waiting for current jobs to finish...')

    def enhance_photos(self):
        use_suffix = 'True' if self.suffix is not None else 'False'
        photoenhance(target=self.target, 
                     output_folder=self.output_folder, 
                     load=self.load, 
                     use_suffix=use_suffix, 
                     suffix=self.suffix,
                     batch_monitor=self.batch_monitor)

    def set_msg_function(self, msg_func):
        self.msg_func = msg_func

    # base method overriden to change the progress max and label at the start
    def run(self):
        try:
            logger.info("start")
            self.progress_value = 0
            self.finished = False
            # self.set_progress_max(10)
            # self.set_progress_value(1)
            self.set_progress_value(0)
            self.set_progress_max(1)
            self.set_progress_label("Initialising...")
            consumer_thread = threading.Thread(target=self.consumer, daemon=True)
            consumer_thread.start()
            result = self._run()
            self.set_progress_value(self.progress_max+1)
            self.finished = True
            logger.info("finish")
            consumer_thread.join()
            logger.info("t joined")
            # self.q.join()
            # logger.info("q joined")
            # self.after_run.emit(result)
            # logger.info("finished thread emitted after run")
        except Exception as e:
            self.exception.emit(e)
