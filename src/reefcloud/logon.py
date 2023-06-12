import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi

from aims import state


from aims import state

from oauthlib.oauth2 import WebApplicationClient, BackendApplicationClient
from threading import Thread
from requests_oauthlib import OAuth2Session
import webbrowser
import logging
from urllib.parse import urlparse, parse_qs
import requests
from jwt import (
    JWT,
    jwk_from_dict,

)


logger = logging.getLogger("")


oauth2_code = None
oauth2_state = None

html = """
<html>
    <head><title>ReefCloud Authentication</title></head>
    <body onload="submit();">
        <p id="message">Waiting for token...</p>
        <script>
            function submit() {
                const queryParamsString = window.location.hash.substr(1);
                var http = new XMLHttpRequest();
                http.open("POST", "/", true);
                http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                http.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        messagePara = document.getElementById("message");
                        messagePara.innerText = "Token received, you can close this window"
                        console.log("Token sent");
                    }
                };
                http.send(queryParamsString);
                console.log("Sent params");
                timeoutID = setTimeout(submit, 1000);
            }
            
        </script>
    </body
</html>
"""
otherhtml = """
<html>
    <head><title>ReefCloud Authentication</title></head>
    <body>
        <p id="message">token received.  Please close this tab or window.</p>

    </body
</html>
"""

tokens=None

class TokenServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        global oauth2_code
        logger.info(f"do_Get {self.path}")
        params = parse_qs(urlparse(self.path).query)
        if 'code' in params:
            oauth2_code = params['code'][0]
            logger.info(f"code: {oauth2_code}")

        logger.info("gonna send response")
        self.send_response(200)
        logger.info("response sent")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        logger.info("headers sent")
        if oauth2_code:
            logger.info("otherhtml")
            self.wfile.write(bytes(otherhtml, "UTF-8"))
        else:
            logger.info("html")
            self.wfile.write(bytes(html, "UTF-8"))
        logger.info("do_get done")

    def do_POST(self):

        logger.info(f"do_Post {self.path}")
        global oauth2_code
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

class LoginWorker(Thread):
    def __init__(self, client_id, cognito_uri, host_name="localhost", port=4200, path="/app/", launch_browser=True):
        logger.info("LoginWorker __init__() start")

        super().__init__()
        self.host_name = host_name
        self.port = port
        self.client_id = client_id
        self.cognito_uri = cognito_uri
        self.path = path
        self.launch_browser = launch_browser
        self.client = WebApplicationClient(client_id=self.client_id)
        # self.client = BackendApplicationClient(client_id=self.client_id)
        self.web_server = None
        logger.info("LoginWorker __init__() end")

        self.oauth_session = None
        self.cancelled = False

    def cancel(self):
        logger.info ("worker cancelled")
        self.cancelled = True
        requests.get("http://localhost:4200")

    def run(self):
        global oauth2_code, oauth2_state
        logger.info("LoginWorker run() start")
        self.oauth_session = OAuth2Session(client=self.client,
                                           redirect_uri=f"http://{self.host_name}:{self.port}{self.path}")
        logger.info(f"http://{self.host_name}:{self.port}{self.path}")
        authorization_url, oauth2_state = self.oauth_session.authorization_url(f"{self.cognito_uri}/login")
        logger.info(f"{authorization_url}")
        if self.launch_browser:
            webbrowser.open(authorization_url)
        else:
            logger.info(f"Please authorize rdp upload here: {authorization_url}")

        self.web_server = HTTPServer((self.host_name, self.port), TokenServer)
        logger.debug(f"Server starting http://{self.host_name}:{self.port}")
        logger.info(f"Server starting http://{self.host_name}:{self.port}")
        while oauth2_code is None and not self.cancelled:
            logger.info("Handling")
            self.web_server.handle_request()

        self.web_server.server_close()
        logger.info("After webserver close")
        logger.info("LoginWorker run() end")

        logger.info("Configured access token and shutdown server")

    def get_session(self):
        return self.oauth_session


class UserInfo():
    def __init__(self, cognito_token_key_url, name, email, authorized=False, message=""):
        self.cognito_token_key_url = cognito_token_key_url
        self.name = name
        self.email = email
        self.authorized = authorized
        self.message = message

    @classmethod
    def _get_jwt_encryption_pub_keys(self, cognito_token_key_url):

        response = requests.get(cognito_token_key_url)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            logger.info(response.json())
            logger.info(type(response.json()))
            return response.json()

    @classmethod
    def from_id_token(cls, cognito_token_key_url, id_token, access_token):
        user_info_url = f'{state.config.api_url}/user_info'

        jwt_object = JWT()
        data = cls._get_jwt_encryption_pub_keys(cognito_token_key_url)
        signing_key = jwk_from_dict(data['keys'][0])
        decoded = jwt_object.decode(id_token, signing_key)
        headers = {
            'Authorization': 'Bearer {}'.format(access_token)
        }

        response = requests.get(user_info_url, headers=headers)
        if response.status_code == 200:
            authorized = True
            message = 'You are a valid Reefcloud user and authorized to upload reefscan data.'
        else:
            authorized = False
            message = str(response.content.decode('UTF-8'))
            logger.info(message)
        return cls(cognito_token_key_url, decoded['name'], decoded['email'], authorized=authorized, message=message)


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
        global oauth2_code, oauth2_state
        self.login_worker = LoginWorker(self.client_id, self.cognito_uri)
        self.login_worker.start()
        self.login_worker.join()
        self.oauth2_session = self.login_worker.get_session()

        token_url = f'{self.cognito_uri}/oauth2/token'
        self.tokens = self.oauth2_session.fetch_token(token_url,
                                                      code=oauth2_code,
                                                      state=oauth2_state,
                                                      client_id=self.client_id,
                                                      include_client_id=True)
        print(self.tokens)
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
