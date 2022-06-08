import traceback

from reefscanner.basic_model.basic_model import BasicModel

from aims.gui_model.hardware_sync_model import HardwareSyncModel
from aims.gui_model.surveys_model import SurveysModel


class GuiModel(BasicModel):
    def __init__(self):
        super().__init__()
        self.surveysModel = SurveysModel()
        self.server_data_folder = ""
        self.hardware_data_folder = ""
        self.slow_network = False
        self.data_loaded = False


    def read_surveys(self, progress_queue, image_folder, json_folder, samba, slow_network):
        surveys_data = super().read_surveys(progress_queue, image_folder, json_folder, samba, slow_network)
        self.surveysModel.data_dict = surveys_data
        return surveys_data


    def make_onboard_sync_model(self):
        onboard_sync_model = HardwareSyncModel()
        onboard_sync_model.sites_lookup = self.surveysModel.sites_lookup.copy()
        onboard_sync_model.projects_lookup = self.surveysModel.projects_lookup
        onboard_sync_model.trips_lookup = self.surveysModel.trips_lookup
        onboard_sync_model.default_project = self.default_project
        onboard_sync_model.trip = self.trip
        onboard_sync_model.auto_save = False
        onboard_sync_model.data_folder = self.hardware_data_folder
        surveys = self.surveysModel.data_array
        if len(surveys) > 0:
            onboard_sync_model.default_operator = surveys[len(surveys) - 1]["operator"]
        else:
            onboard_sync_model.default_operator = ""

        return onboard_sync_model
