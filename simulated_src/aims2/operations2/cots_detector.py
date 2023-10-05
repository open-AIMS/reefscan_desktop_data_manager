import logging

from aims import utils

# Uses a QProcess to start the COTS detector shell script
# QProcess is designed to start in a separate thread and provides signals and slots to monitor and control the process
from aims.operations.abstract_cots_detector import AbstractCotsDetector

logger = logging.getLogger("")


class CotsDetector(AbstractCotsDetector):

    # starts the shell script
    def callProgram(self, survey_path):
        # run the process
        # `start` takes the exec and a list of arguments
        self.output.append("ping 127.0.0.1")
        self.process.start("ping", ["127.0.0.1"])


