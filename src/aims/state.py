from reefscanner.basic_model.basic_model import BasicModel

from aims.config import Config

from aims2.operations2.camera_utils import read_reefscan_id_for_ip


class State:

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.model = BasicModel()
        self.meipass = None
        self.has_meipass = False
        self.surveys_tree = None
        self.reefscan_id = ""
        self.primary_drive = None
        self.backup_drive = None
        self.primary_folder = None
        self.backup_folder = None
        self.reefcloud_session = None
        self.oauth2_code = None
        self.oauth2_state = None
        self.read_only = False
        self.is_simulated = False

    def simulated(self, is_simulated: bool):
        self.read_only = is_simulated and not self.has_meipass
        self.is_simulated = is_simulated

    def meipass_linux(self):
        return self.meipass.replace("\\", "/")

    def set_data_folders(self):
        self.model.set_data_folders(self.primary_folder, self.backup_folder, self.config.hardware_data_folder)

    def read_reefscan_id(self):
        return read_reefscan_id_for_ip(self.config.camera_ip)


state = State()