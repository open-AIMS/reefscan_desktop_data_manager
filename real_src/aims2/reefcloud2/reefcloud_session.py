import logging
from datetime import datetime

from aims.state import state
from reefcloud.logon import LoginWorker, UserInfo

logger = logging.getLogger("")


class ReefCloudSession():
    def __init__(self, client_id, cognito_uri):
        self.client_id = client_id
        self.cognito_uri = cognito_uri
        self.current_user = None
        self.is_logged_in = False
        self.login_worker = None
        self.finished = False

    def cancel(self):
        logger.info ("session cancelled")
        if self.login_worker is not None:
            self.login_worker.cancel()

    def check_refresh(self):
        expire_time = self.tokens["expires_at"]
        now = datetime.timestamp(datetime.now())
        expires_in_secs = expire_time - now
        # if the tokens expire less than a minute from now then refresh
        if expires_in_secs < 60:
            token_url = f'{self.cognito_uri}/oauth2/token'
            tokens = self.oauth2_session.refresh_token(token_url,
                                                          refresh_token=self.tokens["refresh_token"],
                                                       client_id=self.client_id,
                                                       include_client_id=True
                                                       )
            self.tokens = tokens
            self.id_token = self.tokens['id_token']
            self.access_token = self.tokens['access_token']


    def login(self):
        self.login_worker = LoginWorker(self.client_id, self.cognito_uri)
        self.login_worker.start()
        self.login_worker.join()
        self.oauth2_session = self.login_worker.get_session()

        token_url = f'{self.cognito_uri}/oauth2/token'
        self.tokens = self.oauth2_session.fetch_token(token_url,
                                                      code=state.oauth2_code,
                                                      state=state.oauth2_state,
                                                      client_id=self.client_id,
                                                      include_client_id=True)
        logger.info(self.tokens)
        self.id_token = self.tokens['id_token']
        self.access_token = self.tokens['access_token']
        self.current_user = UserInfo.from_id_token(state.config.cognito_token_key_url, self.id_token, self.access_token)
        self.is_logged_in = True
        # Set code to none so if the user clicks the login page a second time, the web server waits for the new code
        code = None
        self.finished = True

    def get(self, url, **kwargs):
        return self.oauth2_session.get(url, **kwargs)

    def options(self, url, **kwargs):
        return self.oauth2_session.options(url, **kwargs)

    def head(self, url, **kwargs):
        return self.oauth2_session.head(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.oauth2_session.post(url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.oauth2_session.put(url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.oauth2_session.patch(url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.oauth2_session.delete(url, **kwargs)
