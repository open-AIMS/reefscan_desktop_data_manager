from aims.config import Config
from aims.gui_model.model import GuiModel
from aims.operations.load_data import load_data, load_camera_data
from fabric import Connection

config = Config()
model = GuiModel()
meipass = None
surveys_tree = None
reefscan_id = ""


def meipass_linux():
    return meipass.replace("\\", "/")


def load_data_model(aims_status_dialog):
    set_data_folders()
    model.camera_samba = config.camera_samba
    model.slow_network = config.slow_network
    model.data_loaded, model.message = load_data(model, config.camera_connected, aims_status_dialog=aims_status_dialog)


def load_camera_data_model(aims_status_dialog):
    model.camera_data_folder = config.hardware_data_folder
    model.data_loaded, model.message = load_camera_data(model, aims_status_dialog=aims_status_dialog)


def set_data_folders():
    model.set_data_folders(config.data_folder, config.backup_data_folder, config.hardware_data_folder)


def read_reefscan_id():
    conn = Connection(
        "jetson@" + config.camera_ip,
        connect_kwargs={"password": "jetson"}
    )

    r = conn.run("cat ~/reefscan_id.txt")
    reefscan_id = r.stdout
    return reefscan_id