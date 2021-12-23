from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.operations.load_data import load_data

config = Config()
model = GuiModel()
meipass = None
trip_dlg = None
surveys_tree = None


def load_data_model(aims_status_dialog):
    model.set_data_folders(config.data_folder, config.hardware_data_folder)
    load_data(model, aims_status_dialog=aims_status_dialog)
