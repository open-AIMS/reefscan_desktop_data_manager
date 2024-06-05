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

        self.language = os.getenv("LANG")
        try:
            if self.language is None:
                windll = ctypes.windll.kernel32
                windll.GetUserDefaultUILanguage()
                self.language = locale.windows_locale[windll.GetUserDefaultUILanguage()]
        except:
            self.language = "eng"

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
            self.projects_details_json_download_url = "https://api.dev.reefcloud.ai/reefcloud/api/organisation/list"
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
            self.projects_details_json_download_url = "https://api.reefcloud.ai/reefcloud/api/organisation/list"
            self.sites_json_download_url = "https://api.reefcloud.ai/reefcloud/api/locations"
            self.project_details_url = "https://api.reefcloud.ai/reefcloud/api/organisation/list"

