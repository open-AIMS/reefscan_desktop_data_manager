import datetime
import logging

from reefcloud.logon import LoginWorker, UserInfo

logger = logging.getLogger("")


class ReefCloudSession():
    def __init__(self, client_id, cognito_uri):
        self.client_id = client_id
        self.cognito_uri = cognito_uri
        self.current_user = None
        self.is_logged_in = False


    def login(self):
        self.is_logged_in = True
        self.current_user = "Fake User"
        self.current_user = UserInfo(None, "Fake User", "fake@gmail.com", True, "This is for demonstration purposes")
