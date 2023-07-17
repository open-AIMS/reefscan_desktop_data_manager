import logging
import string
import threading
import time

from PyQt5.QtCore import QObject
from reefscanner.archive_stats.archive_stats import ArchiveStats

from aims.state import state
from PyQt5 import QtCore

logger = logging.getLogger("")


class ArchiveChecker(QObject):
    progress = QtCore.pyqtSignal(object)

    def __init__(self):
        logger.info("set up check")
        super().__init__()
        self.archive_stats = ArchiveStats()
        self.running = False

    def check(self):
        logger.info("do the check")
        self.running = False

    # def report(self):
    #     while self.running:
    #         stats_string = self.archive_stats.to_string()
    #         self.progress.emit(stats_string)
    #         time.sleep(1)
    #
    #     stats_string = self.archive_stats.to_string()
    #     self.progress.emit(stats_string)
    #
    # def run(self):
    #     self.archive_stats.cancelled = False
    #     if not self.running:
    #         checker_thread = threading.Thread(target=self.check, daemon=True)
    #         checker_thread.start()
    #
    #         report_thread = threading.Thread(target=self.report, daemon=True)
    #         report_thread.start()
    #
    #         # checker_thread.join()
    #         logger.info("finished")
    #
    # def cancel(self):
    #     self.archive_stats.cancelled = True
    #
