from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.operations.load_data import load_data

config = Config()
model = GuiModel()
meipass = None
trip_dlg = None
surveys_tree = None
data_loaded = False


def load_data_model(aims_status_dialog):
    model.set_data_folders(config.data_folder, config.hardware_data_folder)
    model.camera_samba = config.camera_samba
    model.slow_network = config.slow_network
    load_data(model, aims_status_dialog=aims_status_dialog)
    model.data_loaded = True
