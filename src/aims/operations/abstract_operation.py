import logging
import threading

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from reefscanner.basic_model.progress_queue import ProgressQueue

logger = logging.getLogger(__name__)


class AbstractOperation(QObject):
    set_max = QtCore.pyqtSignal(int)
    set_value = QtCore.pyqtSignal(object)
    # after_run = QtCore.pyqtSignal(object)
    exception = QtCore.pyqtSignal(object)

    def __init__(self):
        logger.info("set up sync")
        super().__init__()
        self.progress_queue = ProgressQueue()
        self.finished = True
        self.progress_value = 0
        self.progress_max = 0
        self.progress_label = ""
        self.update_interval = 100
        logger.info("done set up sync")

    def cancel(self):
        print ("abstract operation says cancel")
        logger.info("abstract operation says cancel")
        self.sync.cancel()

    def consumer(self):
        logger.info(f"consumer started {self.progress_value}")
        while not self.finished:
            # time.sleep(0.001)
            try:
                (operation, value) = self.progress_queue.q.get(block=True, timeout=0.1)
                logger.info(f"{operation} {value}")
                if operation == "value":
                    self.progress_value += 1
                    if self.progress_value % self.update_interval == 0:
                        self.set_progress_value(self.progress_value)
                elif operation == "max":
                    self.progress_max = value
                    self.set_progress_max(value)
                elif operation == "label":
                    self.set_progress_label(value)
                self.progress_queue.q.task_done()
            except Exception as e:
                pass
        logger.info("consumer finished")

    def run(self):
        try:
            logger.info("start")
            self.progress_value = 0
            self.finished = False
            self.set_progress_max(10)
            self.set_progress_value(1)
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

    def _run(self):
        pass

    def set_progress_label(self, progress_label, ):
        self.progress_label = progress_label
        # logger.info(f"value {i}")
        self.set_value.emit((self.progress_value, self.progress_label))

    def set_progress_value(self, i):
        # logger.info(f"value {i}")
        self.progress_value = i
        self.set_value.emit((i, self.progress_label))

    def set_progress_max(self, i):
        logger.info(f"max {i}")
        self.progress_max = i
        self.set_max.emit(i)

