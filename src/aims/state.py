from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.operations.load_data import load_data

config = Config()
model = GuiModel()
meipass = None
surveys_tree = None


def load_data_model(aims_status_dialog):
    model.set_data_folders(config.data_folder, config.hardware_data_folder)
    model.camera_samba = config.camera_samba
    model.slow_network = config.slow_network
    model.default_vessel = config.default_vessel
    model.default_operator = config.default_operator
    model.default_observer = config.default_observer
    model.data_loaded, model.message = load_data(model, config.camera_connected, aims_status_dialog=aims_status_dialog)
