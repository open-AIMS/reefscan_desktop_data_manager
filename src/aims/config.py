from reefscanner.basic_model.json_utils import write_json_file
from reefscanner.basic_model.json_utils import read_json_file

class Config(object):

    def __init__(self, model):
        super().__init__()
        self.config_folder = "c:/aims/reef-scanner"
        self.config_file_name = "config.json"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.read_config_file(model)

    def save_config_file(self, model):
        data_folder_json = {
            "data_folder": model.data_folder,
            "hardware_data_folder": model.hardware_data_folder,
            "server_data_folder": model.server_data_folder
        }
        write_json_file(self.config_folder, self.config_file_name, data_folder_json)

    def read_config_file(self, model):
        try:
            data_folder_json = read_json_file(self.config_file)
        except:
            data_folder_json = {}

        model.data_folder = data_folder_json.get("data_folder", "c:/aims/reef-scanner")
        model.hardware_data_folder = data_folder_json.get("hardware_data_folder", "c:/aims/reef-scanner/ONBOARD")
        model.server_data_folder = data_folder_json.get("server_data_folder", "c:/aims/reef-scanner/SERVER")
