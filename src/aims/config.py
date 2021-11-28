from reefscanner.basic_model.json_utils import write_json_file
from reefscanner.basic_model.json_utils import read_json_file


class Config(object):

    def __init__(self):
        super().__init__()
        self.config_folder = "c:/aims/reef-scanner"
        self.config_file_name = "config.json"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.data_folder = None
        self.hardware_data_folder = None
        self.server_data_folder = None

        self.read_config_file()

    def save_config_file(self):
        data_folder_json = {
            "data_folder": self.data_folder,
            "hardware_data_folder": self.hardware_data_folder,
            "server_data_folder": self.server_data_folder
        }
        write_json_file(self.config_folder, self.config_file_name, data_folder_json)

    def read_config_file(self):
        try:
            data_folder_json = read_json_file(self.config_file)
        except:
            data_folder_json = {}

        self.data_folder = data_folder_json.get("data_folder", "c:/aims/reef-scanner")
        self.hardware_data_folder = data_folder_json.get("hardware_data_folder", "c:/aims/reef-scanner/ONBOARD")
        self.server_data_folder = data_folder_json.get("server_data_folder", "c:/aims/reef-scanner/SERVER")
