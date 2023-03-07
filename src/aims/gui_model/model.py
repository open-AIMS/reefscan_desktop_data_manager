

from reefscanner.basic_model.basic_model import BasicModel

from aims.gui_model.hardware_sync_model import HardwareSyncModel
from aims.gui_model.surveys_model import SurveysModel


class GuiModel(BasicModel):
    def __init__(self):
        super().__init__()
        self.surveysModel = SurveysModel()
        self.server_data_folder = ""
        self.slow_network = False
        self.data_loaded = False

    def read_surveys(self, progress_queue, image_folder, backup_folder, json_folder, samba, slow_network):
        surveys_data = super().read_surveys(progress_queue, image_folder, backup_folder, json_folder, samba, slow_network)
        self.surveysModel.data_dict = surveys_data
        return surveys_data

