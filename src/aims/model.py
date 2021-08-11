import datetime
import os
import traceback

import shortuuid

from aims.surveys_model import SurveysModel
from aims.sites_model import SitesModel
from aims.json_utils import read_json_file, write_json_file


class Model(object):
    data_folder = ""
    trip = {}
    surveysModel = SurveysModel()
    sitesModel = SitesModel()
    default_project = ""

    def set_data_folder(self, data_folder):
        if os.path.isdir(data_folder):
            self.data_folder = data_folder
            print(data_folder)
            self.read_from_files()

    def read_from_files(self):
        self.readTrip()
        self.read_projects()

        try:
            self.surveysModel.read_data(self.data_folder)
        except Exception as e:
            self.surveysModel.data = []
            print(e)

        self.read_sites()

    def read_projects(self):
        try:
            projects = read_json_file(f"{self.data_folder}/projects.json")
            self.surveysModel.projects_lookup = {project["id"]: project["name"] for project in projects}
            print (self.surveysModel.projects_lookup)
            self.default_project = projects[0]["id"]
        except:
            traceback.print_exc()
            self.surveysModel.projects_lookup = {}

    def read_sites(self):
        try:
            self.sitesModel.read_data(self.data_folder)
        except Exception as e:
            self.sitesModel.data = []
            print(e)
        self.make_sites_lookup()

    def make_sites_lookup(self):
        self.surveysModel.sites_lookup = {site["uuid"]: site["name"] for site in self.sitesModel.data_array}

    def makeTripsLookup(self):
        self.surveysModel.trips_lookup = {self.trip["uuid"]: self.trip["name"]}

    def saveTrip(self):
        trip = self.trip.copy()
        uuid = trip.pop('uuid')
        folder = trip.pop('folder')
        trip["start_date"] = datetime.date.strftime(self.trip["start_date"], "%Y-%m-%d")
        trip["finish_date"] = datetime.date.strftime(self.trip["finish_date"], "%Y-%m-%d")

        write_json_file(folder, 'trip.json', trip)

    def readTrip(self):
        tripsFolder = f'{self.data_folder}/trips'
        if not os.path.isdir(tripsFolder):
            os.mkdir(tripsFolder)

        tripFolders = os.listdir(tripsFolder)
        if len(tripFolders) == 0:
            uuid = shortuuid.uuid()
            os.mkdir(f'{tripsFolder}/{uuid}')
        else:
            uuid = tripFolders[0]

        tripFileName = f'{tripsFolder}/{uuid}/trip.json'


        if os.path.exists(tripFileName):
            self.trip = read_json_file(tripFileName)
            self.trip["start_date"] = datetime.datetime.strptime(self.trip["start_date"], "%Y-%m-%d").date()
            self.trip["finish_date"] = datetime.datetime.strptime(self.trip["finish_date"], "%Y-%m-%d").date()
            new_trip = False
        else:
            today = datetime.date.today()
            self.trip = {"name": "EDIT THIS TRIP", "start_date": today, "vessel": "", "finish_date": today + datetime.timedelta(days=7)}
            new_trip = True

        self.trip["folder"] = f'{tripsFolder}/{uuid}'
        self.trip["uuid"] = uuid

        if new_trip:
            self.saveTrip()

        self.makeTripsLookup()

    def getTripDesc(self):
        try:
            desc = f'{self.trip["name"]} {self.trip["vessel"]} from {self.trip["start_date"]}'
            desc=f'{desc} to {self.trip["finish_date"]}'
            return desc
        except Exception as e:
            print(e)
            return ""
