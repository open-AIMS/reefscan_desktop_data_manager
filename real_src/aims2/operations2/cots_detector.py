import logging
import os

from reefscanner.basic_model.model_utils import replace_last

from aims import utils

# Uses a QProcess to start the COTS detector shell script
# QProcess is designed to start in a separate thread and provides signals and slots to monitor and control the process
from aims.operations.abstract_cots_detector import AbstractCotsDetector

logger = logging.getLogger("")


class CotsDetector(AbstractCotsDetector):

    # starts the shell script
    def callProgram(self, survey_path):
        # run the process
        script = "/home/reefscan/cots-detector-two-cameras.sh"
        output_path = replace_last(survey_path, "/reefscan/", "/reefscan_eod_cots/")
        input_path = survey_path

        os.makedirs(f"{output_path}/cam_1", exist_ok=True)
        os.makedirs(f"{output_path}/cam_2", exist_ok=True)
        self.output.append(f'bash {script} "{input_path}" "{output_path}"')
        # `start` takes the exec and a list of arguments
        self.process.start("bash", [script, f"{input_path}", f"{output_path}"])

