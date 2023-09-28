from PyQt5.QtCore import QObject, QProcess, QByteArray
from PyQt5.QtWidgets import QTextEdit, QTextBrowser

from aims import utils

# Uses a QProcess to start the COTS detector shell script
# QProcess is designed to start in a separate thread and provides signals and slots to monitor and control the process
from aims.operations.BatchResult import BatchResult


class CotsDetector:

    def __init__(self, output: QTextEdit, parent: QObject, enable_function, disable_function):
        super().__init__()
        self.output: QTextBrowser = output
        self.process = QProcess(parent)
        self.process.readyReadStandardOutput.connect(self.outputReady)
        self.process.readyReadStandardError.connect(self.errorReady)
        self.process.errorOccurred.connect(self.error_occured)
        self.process.stateChanged.connect(self.handle_state)
        self.enable_function = enable_function
        self.disable_function = disable_function
        self.batch_result = BatchResult()

# Picks up errors that are not written to standard error
    def error_occured(self, error: QProcess.ProcessError):
        errors = {
            QProcess.FailedToStart: "Failed To Start",
            QProcess.Crashed: "Crashed",
            QProcess.Timedout: "Timed out",
            QProcess.WriteError: "Write Error",
            QProcess.ReadError: "Read Error",
            QProcess.UnknownError: "Unknown Error"
        }
        error_desc = errors[error]
        self.output.append(error_desc)

# Disable the UI whil it is running
    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        print(f"State changed: {state_name}")
        if state == QProcess.NotRunning:
            self.enable_function()
            self.batch_result.finished = True
        else:
            self.disable_function()
            self.batch_result.finished = False
            self.batch_result.cancelled = False

# write standard output to the output text box
    def outputReady(self):
        print("some data")
        data: QByteArray = self.process.readAllStandardOutput()
        print(data)
        self.output.append(str(data.data(), 'utf-8'))

# write standard error to the output text box
# we could consider having a different text box for errors
    def errorReady(self):
        print("error data")
        data: QByteArray = self.process.readAllStandardError()
        self.output.append(str(data.data(), 'utf-8'))
        print(data)

# starts the shell script
    def callProgram(self, survey_path):
        # run the process
        # `start` takes the exec and a list of arguments
        script = "/home/reefscan/cots-detector.sh"
        output_path = utils.replace_last(survey_path, "/reefscan/", "/reefscan_eod_cots/")
        input_path = survey_path
        self.output.append(f'bash {script} "{input_path}" "{output_path}"')
        self.process.start("bash", [script, input_path, output_path])
# leaving this here because it is useful while testing on windows
#        self.process.start("ping", ["127.0.0.1"])

# cancel the process
    def cancel(self):
        self.batch_result.canceled = True
        self.process.kill()
