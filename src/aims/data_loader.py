from aims.operations.load_data import load_data, load_camera_data, load_archive_data
from aims.state import state
import logging
logger = logging.getLogger("")
def load_data_model(aims_status_dialog):
    state.model.slow_network = False
    return load_data(state.model, False, aims_status_dialog=aims_status_dialog)


def load_camera_data_model(aims_status_dialog):
    state.model.camera_data_folder = state.config.hardware_data_folder
    return load_camera_data(state.model, aims_status_dialog=aims_status_dialog)


def load_archive_data_model(aims_status_dialog):
    state.model.camera_data_folder = state.config.hardware_data_folder
    return load_archive_data(state.model, aims_status_dialog=aims_status_dialog)

