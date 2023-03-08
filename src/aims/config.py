from pathlib import Path

import requests
from reefscanner.basic_model.json_utils import write_json_file
from reefscanner.basic_model.json_utils import read_json_file


class Config(object):

    def __init__(self):
        super().__init__()
        self.config_folder = str(Path.home()) + "/.aims/reefscan"
        self.config_file_name = "config.json"
        self.reefcloud_projects_filename = "reefcloud_projects.json"
        self.reefcloud_sites_filename = "reefcloud_sites.json"

        self.config_file = f"{self.config_folder}/{self.config_file_name}"
        self.camera_connected = True

        self.data_folder = None
        # self.hardware_data_folder = r"\\10.42.0.1\data"
        # self.hardware_data_folder = r"\\192.168.1.254\data"
        self.camera_ip = "192.168.3.2"
        self.camera_images_folder = "/media/jetson/data" \
                                    "/images"
        self.hardware_data_folder = r"\\192.168.3.2\images"
        # self.hardware_data_folder = r"\\xavier\data"
        # self.hardware_data_folder = r"\\169.254.100.1\data"
        self.camera_samba = True

        # self.hardware_data_folder = r"C:\temp\photos_in"
        # self.camera_samba = False

        # Configuration for AWS

        self.client_id = '4g2uk4maadbqvuoep86ov2mig8'
        self.cognito_uri = 'https://reefscan1.auth.ap-southeast-2.amazoncognito.com'

        self.projects_json_download_url = "http://api.dev.reefcloud.aieee/reefcloud/api/organisation/list?org=REEFSCAN"
        self.sites_json_download_url = "http://api.dev.reefcloud.aieee/reefcloud/api/locations?org=REEFSCAN"


        #self.authorization_url = f'{self.cognito_uri}/authorize'
        self.token = ""


        self.backup_data_folder = None
        self.default_operator = None
        self.default_observer = None
        self.default_vessel = None

        self.backup = True
        self.time_zone = ""

        self.read_config_file()

    def save_config_file(self):
        data_folder_json = {
            "data_folder": self.data_folder,
            "camera_connected": self.camera_connected,
            "backup_data_folder": self.backup_data_folder,
            "slow_network": self.slow_network,
            "default_operator": self.default_operator,
            "default_observer": self.default_observer,
            "default_vessel": self.default_vessel,
            "hardware_data_folder": self.hardware_data_folder,
            "backup": self.backup,
            "time_zone": self.time_zone

        }
        write_json_file(self.config_folder, self.config_file_name, data_folder_json)

    def read_config_file(self):
        try:
            data_folder_json = read_json_file(self.config_file)
        except:
            data_folder_json = {}

        home = str(Path.home())
        self.data_folder = data_folder_json.get("data_folder", home + "/REEFSCAN/local")
        self.backup_data_folder = data_folder_json.get("backup_data_folder", home + "/REEFSCAN/backup")
        self.slow_network = data_folder_json.get("slow_network", False)
        self.camera_connected = data_folder_json.get("camera_connected",True)
        self.default_operator = data_folder_json.get("default_operator", "")
        self.default_observer = data_folder_json.get("default_observer", "")
        self.default_vessel = data_folder_json.get("default_vessel", "")
        self.hardware_data_folder = data_folder_json.get("hardware_data_folder", r"\\192.168.3.2\images")
        self.backup = data_folder_json.get("backup", True)
        self.time_zone = data_folder_json.get("time_zone", "")
        self.reefcloud_projects = self.read_reefcloud_projects()
        self.reefcloud_sites = self.read_reefcloud_sites()

        print(self)

    def read_reefcloud_projects(self):
        projects = {}
        try:
            reefcloud_projects_json = read_json_file(self.config_folder + "/" + self.reefcloud_projects_filename)
        except Exception as e:
            reefcloud_projects_json = {}
        for project in reefcloud_projects_json:
            projects[project['name']] = project['id']

        return projects

    def read_reefcloud_sites(self):
        sites = {}
        try:
            reefcloud_sites_json = read_json_file(self.config_folder + "/" + self.reefcloud_sites_filename)
        except:
            reefcloud_sites_json = {}
        for site in reefcloud_sites_json:
            sites[site['name']] = site['id']
        return sites

    def update_reefcloud_projects(self):
        # The real url will be something like https://api.dev.reefcloud.ai/reefcloud/api/organisation/list?org=REEFSCAN
        try:
            url = self.projects_json_download_url
            r = requests.get(url)
            if r.status_code == 200:
                filename = self.config_folder + "/" + self.reefcloud_projects_filename
                with open(filename, 'w') as f:
                    f.write(r.text)
                    f.close()
                    return True
        except Exception as e:
            print(e)
            print(type(e))
        return False

    def update_reefcloud_sites(self):
        # The real url will be something like https://api.dev.reefcloud.ai/reefcloud/api/locations?org=REEFSCAN
        # url = "https://api.dev.reefcloud.ai/reefcloud/api/locations?org=REEFSCAN"
        # r = requests.get(url)
        # temp = tempfile.TemporaryFile()
        # print(temp)
        # print(temp.name)
        # temp.write(r.txt)
        # filename = temp.name
        # temp.close()
        try:
            url = self.sites_json_download_url
            r = requests.get(url)
            if r.status_code == 200:
                filename = self.config_folder + "/" + self.reefcloud_sites_filename
                with open(filename, 'w') as f:
                    f.write(r.text)
                    f.close()
                    return True
        except Exception as e:
            print(e)
            print(type(e))
        return False

    def valid_reefcloud_project(self, project_name):
        if project_name in self.reefcloud_projects:
            return True
        else:
            return False

    def valid_reefcloud_site(self, site_name):
        if site_name in self.reefcloud_sites:
            return True
        else:
            return False