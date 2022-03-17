import traceback

from reefscanner.basic_model.basic_model import BasicModel
from reefscanner.basic_model.reader_writer import save_site

from aims.gui_model.hardware_sync_model import HardwareSyncModel
from aims.gui_model.methods_model import MethodsModel
from aims.gui_model.project_model import ProjectsModel
from aims.gui_model.surveys_model import SurveysModel
from aims.gui_model.sites_model import SitesModel


class GuiModel(BasicModel):
    def __init__(self):
        super().__init__()
        self.surveysModel = SurveysModel()
        self.sitesModel = SitesModel()
        self.methodsModel = MethodsModel()
        self.projects_model = ProjectsModel()
        self.server_data_folder = ""
        self.hardware_data_folder = ""
        self.slow_network = False
        self.data_loaded = False

    def add_new_sites(self, new_sites):
        for site in new_sites:
            self.add_new_site(site)

    def add_new_site(self, site):
        site["folder"] = f"{self.data_folder}/sites/{site['uuid']}"
        save_site(site, self.sites_data_array)

    def read_surveys(self, progress_queue, image_folder, json_folder, samba, slow_network):
        surveys_data = super().read_surveys(progress_queue, image_folder, json_folder, samba, slow_network)
        self.surveysModel.data_dict = surveys_data
        return surveys_data

    def read_trip(self):
        super().read_trip()
        self.make_trips_lookup()

    def read_sites(self):
        super().read_sites()
        self.make_sites_lookup()
        self.sitesModel.data_array = self.sites_data_array

    def read_methods(self):
        super().read_methods()
        self.make_methods_lookup()
        self.methodsModel.data_array = self.methods_data_array

    def read_projects(self):
        try:
            super().read_projects()
            self.surveysModel.projects_lookup = {project["id"]: project["name"] for project in self.projects}
            print(self.surveysModel.projects_lookup)
            self.surveysModel.default_project = self.default_project
            self.projects_model.data_array = self.projects
        except:
            traceback.print_exc()
            self.surveysModel.projects_lookup = {}

    def make_sites_lookup(self):
        self.surveysModel.sites_lookup = {site["uuid"]: site["name"] for site in self.sites_data_array}

    def make_methods_lookup(self):
        self.surveysModel.method_lookup = {method["uuid"]: method["name"] for method in self.methods_data_array}

    def make_trips_lookup(self):
        self.surveysModel.trips_lookup = {self.trip["uuid"]: self.trip["name"]}

    def get_trip_desc(self):
        try:
            desc = f'{self.trip["name"]} {self.trip["vessel"]} from {self.trip["start_date"]}'
            desc=f'{desc} to {self.trip["finish_date"]}'
            return desc
        except Exception as e:
            print(e)
            return ""

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
