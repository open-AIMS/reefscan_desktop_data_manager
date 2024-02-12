import locale
import logging
import os
from pathlib import Path

import requests
from reefscanner.basic_model.json_utils import write_json_file
from reefscanner.basic_model.json_utils import read_json_file
import ctypes
logger = logging.getLogger("")
class Config(object):

    def __init__(self):
        super().__init__()
        self.config_folder = str(Path.home()) + "/.aims/reefscan"
        self.config_file_name = "config.json"
        self.reefcloud_projects_filename = "reefcloud_projects.json"
        self.reefcloud_sites_filename = "reefcloud_sites.json"

        self.config_file = f"{self.config_folder}/{self.config_file_name}"

        self.camera_ip = "192.168.3.2"
        self.hardware_data_folder = r"\\192.168.3.2\images"

        # self.camera_ip = "10.42.0.1"
        # self.hardware_data_folder = r"\\10.42.0.1\images"

        # Configuration for AWS
        # Projects have write access

        self.dev = False
        self.aws_region_id = ''
        self.cognito_user_pool_id = ''
        self.client_id = ''
        self.cognito_uri = ''
        self.cognito_token_key_url = ''
        
        self.token = ""

        self.backup = True
        self.time_zone = ""
        self.camera_samba = True

        self.deep = False
        self.clear_reefcloud = False
        self.reef_cloud_max_depth = 10

        self.read_config_file()
        self.language = os.getenv("LANG")
        if self.language is None:
            windll = ctypes.windll.kernel32
            windll.GetUserDefaultUILanguage()
            self.language = locale.windows_locale[windll.GetUserDefaultUILanguage()]

        self.vietnemese = self.language == "vi_VN"


        logger.info(self.language)

    def set_deep(self, deep):
        self.deep = deep
        if deep:
            self.camera_ip = "192.168.2.12"
            self.hardware_data_folder = r"\\192.168.2.12\images"

    def set_dev(self, dev):
        self.dev = dev
        if dev:
            self.aws_region_id = 'ap-southeast-2'
            self.cognito_user_pool_id = 'ap-southeast-2_VpzWNPszV'
            self.client_id = '40da2ahdtt0k1h1iro3n98bja3'
            self.cognito_uri = 'https://login.dev.reefcloud.ai/'
            self.cognito_token_key_url = f'https://cognito-idp.{self.aws_region_id}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json'
            self.api_url = 'https://dev.reefscan.api.aims.gov.au/reefscan/api'
            self.projects_json_download_url = "https://api.dev.reefcloud.ai/reefcloud/api/user/access?min-level=WRITE"
            self.sites_json_download_url = "https://api.dev.reefcloud.ai/reefcloud/api/locations"
            self.project_details_url = "https://api.dev.reefcloud.ai/reefcloud/api/organisation/list"

        else:
            self.aws_region_id = 'ap-southeast-2'
            self.cognito_user_pool_id = 'ap-southeast-2_rS47RmMsG'
            self.client_id = '5lu64jpa1vemmfoq8hhkkkpqlg'
            self.cognito_uri = 'https://login.reefcloud.ai/'
            self.cognito_token_key_url = f'https://cognito-idp.{self.aws_region_id}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json'
            self.api_url = 'https://reefscan.api.aims.gov.au/reefscan/api'
            self.projects_json_download_url = "https://api.reefcloud.ai/reefcloud/api/user/access?min-level=WRITE"
            self.sites_json_download_url = "https://api.reefcloud.ai/reefcloud/api/locations"
            self.project_details_url = "https://api.reefcloud.ai/reefcloud/api/organisation/list"

    def save_config_file(self):
        data_folder_json = {
            "backup": self.backup,
            "reef_cloud_max_depth": self.reef_cloud_max_depth
        }
        write_json_file(self.config_folder, self.config_file_name, data_folder_json)

    def read_config_file(self):
        try:
            data_folder_json = read_json_file(self.config_file)
        except:
            data_folder_json = {}

        home = str(Path.home())
        self.backup = data_folder_json.get("backup", True)
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
            reefcloud_projects_json = read_json_file(self.config_folder + "/" + self.reefcloud_projects_filename)
        except Exception as e:
            reefcloud_projects_json = {}
        if 'WRITE' in reefcloud_projects_json and 'ADMIN' in reefcloud_projects_json:
            return reefcloud_projects_json['WRITE'] + reefcloud_projects_json['ADMIN']
        elif 'WRITE' in reefcloud_projects_json:
            return reefcloud_projects_json['WRITE']
        elif 'ADMIN' in reefcloud_projects_json:
            return reefcloud_projects_json['ADMIN']
        else:
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
        if project_name in self.reefcloud_projects:
            return True
        else:
            return False

    def valid_reefcloud_site(self, site_id, project_name):
        for site in self.reefcloud_sites[project_name]:
            if site_id == site["id"]:
                return True

        return False
