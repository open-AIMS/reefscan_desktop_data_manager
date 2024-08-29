import os
from logging.handlers import RotatingFileHandler

from reefscanner.basic_model.basic_model import BasicModel
from reefscanner.basic_model.json_utils import read_json_file

from aims.config import Config
from aims.utils import write_json_file

from aims2.operations2.camera_utils import read_reefscan_id_for_ip
import logging
logger = logging.getLogger("")

class State:

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.model = BasicModel()
        self.meipass = None
        self.has_meipass = False
        self.surveys_tree = None
        self.reefscan_id = ""
        self.primary_drive = None
        self.backup_drive = None
        self.primary_folder = None
        self.backup_folder = None
        self.reefcloud_session = None
        self.oauth2_code = None
        self.oauth2_state = None
        self.read_only = False
        self.is_simulated = False

        self.config_file_name = "reefscan_config.json"
        self.reefcloud_projects_filename = "reefcloud_projects.json"
        self.reefcloud_sites_filename = "reefcloud_sites.json"

        self.config_folder = None
        self.config_file = None
        self.reef_cloud_max_depth = 10

    def simulated(self, is_simulated: bool):
        self.read_only = is_simulated and not self.has_meipass
        self.is_simulated = is_simulated

    def meipass_linux(self):
        return self.meipass.replace("\\", "/")

    def set_data_folders(self):
        self.model.set_data_folders(self.primary_folder, self.backup_folder, self.config.hardware_data_folder)
        self.config_folder = f"{self.primary_drive}/config"
        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.read_config_file()

        if not os.path.isdir(self.config_folder):
            os.makedirs(self.config_folder)
        path = f"{self.config_folder}/reefscan.log"
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        handler = RotatingFileHandler(path, maxBytes=1000000,
                                      backupCount=5)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def read_reefscan_id(self):
        return read_reefscan_id_for_ip(self.config.camera_ip)

    def save_config_file(self):
        data_folder_json = {
            "reef_cloud_max_depth": self.reef_cloud_max_depth
        }
        write_json_file(self.config_file, data_folder_json)

    def read_config_file(self):
        try:
            data_folder_json = read_json_file(self.config_file)
        except:
            data_folder_json = {}

        self.reef_cloud_max_depth = data_folder_json.get("reef_cloud_max_depth")
        if self.reef_cloud_max_depth is None:
            self.reef_cloud_max_depth = "10"
        self.load_reefcloud_projects()
        self.load_reefcloud_sites()
        logger.info(self)


    def load_reefcloud_projects(self):
        self.reefcloud_projects = self.read_reefcloud_projects()
    def load_reefcloud_sites(self):
        self.reefcloud_sites = self.read_reefcloud_sites()

    def read_reefcloud_projects(self):
        projects = []
        try:
            return read_json_file(self.config_folder + "/" + self.reefcloud_projects_filename)
        except Exception as e:
            return []


    def read_reefcloud_sites(self):
        sites = {}
        try:
            reefcloud_sites_json = read_json_file(self.config_folder + "/" + self.reefcloud_sites_filename)
        except:
            reefcloud_sites_json = {}
        for project in reefcloud_sites_json:
            sites[project] = []
            for site in reefcloud_sites_json[project]:
                sites[project].append({"name": site['name'], "id": site["id"]})
        return sites

    def valid_reefcloud_project(self, project_name):
        for reefcloud_project in self.reefcloud_projects:
            if reefcloud_project["cognito_group"] == project_name:
                return True
        return False

    def valid_reefcloud_site(self, site_id, project_name):
        for site in self.reefcloud_sites[project_name]:
            if site_id == site["id"]:
                return True

        return False


state = State()