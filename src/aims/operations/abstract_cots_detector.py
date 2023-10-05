from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject, QProcess, QByteArray
from PyQt5.QtWidgets import QTextEdit, QTextBrowser

from aims.operations.BatchResult import BatchResult


class AbstractCotsDetector(metaclass=ABCMeta):
    def __init__(self, output: QTextEdit, parent: QObject):
        super().__init__()
        self.output: QTextBrowser = output
        self.process = QProcess(parent)
        self.process.readyReadStandardOutput.connect(self.outputReady)
        self.process.readyReadStandardError.connect(self.errorReady)
        self.process.errorOccurred.connect(self.error_occured)
        self.process.stateChanged.connect(self.handle_state)
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
            self.batch_result.finished = True
        else:
            self.batch_result.finished = False
            self.batch_result.cancelled = False

    # write standard output to the output text box
    def outputReady(self):
        print("some data")
        data: QByteArray = self.process.readAllStandardOutput()
        print(data)
        self.output.append(str(data.data(), 'utf-8'))

    # we could consider having a different text box for errors
    # write standard error to the output text box
    def errorReady(self):
        print("error data")
        data: QByteArray = self.process.readAllStandardError()
        self.output.append(str(data.data(), 'utf-8'))
        print(data)

    @abstractmethod
    # starts the shell script
    def callProgram(self, survey_path):
        pass

    # cancel the process
    def cancel(self):
        self.batch_result.canceled = True
        self.process.kill()