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
        script = "/home/reefscan/cots-detector.sh"
        output_path = utils.replace_last(survey_path, "/reefscan/", "/reefscan_eod_cots/")
        input_path = survey_path
        self.output.append(f'bash {script} "{input_path}" "{output_path}"')
        # `start` takes the exec and a list of arguments
        self.process.start("bash", [script, input_path, output_path])


