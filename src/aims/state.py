from reefscanner.basic_model.basic_model import BasicModel

from aims.config import Config
from aims.operations.load_data import load_data, load_camera_data, load_archive_data
from fabric import Connection

config = Config()
model = BasicModel()
meipass = None
surveys_tree = None
reefscan_id = ""
primary_drive = ""
backup_drive = ""
primary_folder = ""
backup_folder = ""


def meipass_linux():
    return meipass.replace("\\", "/")


def load_data_model(aims_status_dialog):
    model.slow_network = False
    return load_data(model, False, aims_status_dialog=aims_status_dialog)


def load_camera_data_model(aims_status_dialog):
    model.camera_data_folder = config.hardware_data_folder
    return load_camera_data(model, aims_status_dialog=aims_status_dialog)

def load_archive_data_model(aims_status_dialog):
    model.camera_data_folder = config.hardware_data_folder
    return load_archive_data(model, aims_status_dialog=aims_status_dialog)

def set_data_folders():
    model.set_data_folders(primary_folder, backup_folder, config.hardware_data_folder)


def read_reefscan_id():
    try:
        conn = Connection(
            "jetson@" + config.camera_ip,
            connect_kwargs={"password": "jetson"}
        )

        r = conn.run("cat ~/reefscan_id.txt", hide=True)
        reefscan_id = r.stdout
        return reefscan_id
    except:
        return "REEFSCAN"
