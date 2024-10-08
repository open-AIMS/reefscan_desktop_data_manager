import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi

from PyQt5.QtCore import QObject

from aims.state import state


from aims.state import state

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



html = """
<html>
    <head><title>ReefCloud Authentication</title></head>
    <body onload="submit();">
        <p id="message">Waiting...</p>
        <script>
            function submit() {
                const queryParamsString = window.location.hash.substr(1);
                var http = new XMLHttpRequest();
                http.open("POST", "/", true);
                http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                http.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        messagePara = document.getElementById("message");
                        messagePara.innerText = "Log in was successful, you can close this window"
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
        <p id="message">Log in was successful.  Please close this tab or window.</p>

    </body
</html>
"""

tokens=None

class TokenServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        logger.info(f"do_Get {self.path}")
        params = parse_qs(urlparse(self.path).query)
        if 'code' in params:
            state.oauth2_code = params['code'][0]
            logger.info(f"code: {state.oauth2_code}")

        logger.info("gonna send response")
        self.send_response(200)
        logger.info("response sent")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        logger.info("headers sent")
        if state.oauth2_code:
            logger.info("otherhtml")
            self.wfile.write(bytes(otherhtml, "UTF-8"))
        else:
            logger.info("html")
            self.wfile.write(bytes(html, "UTF-8"))
        logger.info("do_get done")

    def do_POST(self):

        logger.info(f"do_Post {self.path}")
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
        try:
            requests.get("http://localhost:4200")
        except:
            pass

    def run(self):
        logger.info("LoginWorker run() start")
        self.oauth_session = OAuth2Session(client=self.client,
                                           redirect_uri=f"http://{self.host_name}:{self.port}{self.path}")
        logger.info(f"http://{self.host_name}:{self.port}{self.path}")
        authorization_url, state.oauth2_state = self.oauth_session.authorization_url(f"{self.cognito_uri}/login")
        logger.info(f"{authorization_url}")
        if self.launch_browser:
            webbrowser.open(authorization_url)
        else:
            logger.info(f"Please authorize rdp upload here: {authorization_url}")

        self.web_server = HTTPServer((self.host_name, self.port), TokenServer)

        logger.info(f"Server starting http://{self.host_name}:{self.port}")
        while state.oauth2_code is None and not self.cancelled:
            logger.info("Handling")
            self.web_server.handle_request()

        self.web_server.server_close()
        logger.info("After webserver close")
        logger.info("LoginWorker run() end")

        logger.info("Configured access token and shutdown server")

    def get_session(self):
        return self.oauth_session


class UserInfo(QObject):
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
        name_ = "Unknown name"
        email_ = "unknown email"
        try:
            user_info_url = f'{state.config.api_url}/user_info'

            jwt_object = JWT()
            data = cls._get_jwt_encryption_pub_keys(cognito_token_key_url)
            signing_key = jwk_from_dict(data['keys'][0])
            decoded = jwt_object.decode(id_token, signing_key)
            name_ = decoded.get('name')
            email_ = decoded.get('email')

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
            return cls(cognito_token_key_url, name_, email_, authorized=authorized, message=message)
        except Exception as e:
            logger.error("Error decoding tokens. ", e)
            return cls(cognito_token_key_url, name_, email_, authorized=False, message=str(e))


