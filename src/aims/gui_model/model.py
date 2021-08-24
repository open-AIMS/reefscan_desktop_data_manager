import traceback

from reefscanner.basic_model.basic_model import BasicModel
from aims.gui_model.surveys_model import SurveysModel
from aims.gui_model.sites_model import SitesModel


class GuiModel(BasicModel):
    surveysModel = SurveysModel()
    sitesModel = SitesModel()

    def read_surveys(self, set_progress_status):
        super().read_surveys(set_progress_status)
        self.surveysModel.data_array = self.surveys_data_array

    def read_trip(self):
        super().read_trip()
        self.make_trips_lookup()

    def read_sites(self):
        super().read_sites()
        self.make_sites_lookup()
        self.sitesModel.data_array = self.sites_data_array

    def read_projects(self):
        try:
            super().read_projects()
            self.surveysModel.projects_lookup = {project["id"]: project["name"] for project in self.projects}
            print(self.surveysModel.projects_lookup)
            self.surveysModel.default_project = self.default_project
        except:
            traceback.print_exc()
            self.surveysModel.projects_lookup = {}

    def make_sites_lookup(self):
        self.surveysModel.sites_lookup = {site["uuid"]: site["name"] for site in self.sites_data_array}

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
