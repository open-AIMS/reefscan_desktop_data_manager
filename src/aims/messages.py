from PyQt5.QtCore import QObject


class Messages(QObject):

    def __init__(self):
        super().__init__()

    def load_camera_data_message(self):
        return self.tr("Reading data from camera")

    def load_camera_data_error_message(self):
        return self.tr("Error can't find camera. Make sure the computer is connected to the camera via an ethernet cable. You may need to restart the camera.")

    def load_local_data_message(self):
        return self.tr("Reading data from local file system")

    def load_local_data_error_message(self):
        return self.tr("Error can't find local files")

    def upload_survey_message(self):
        return self.tr("Uploading survey")

    def copying(self):
        return self.tr("copying")

    def skipping(self):
        return self.tr("skipping")

    def survey(self):
        return self.tr("Survey")

    def of(self):
        return self.tr("of")

messages = Messages()