from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi


api_url = 'https://xx6zbht7ue.execute-api.ap-southeast-2.amazonaws.com/prod/reefscan/api'
user_info_url = f'{api_url}/user_info'


from oauthlib.oauth2 import WebApplicationClient
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


logger = logging.getLogger(__name__)
cognito_uri = 'https://reefscan1.auth.ap-southeast-2.amazoncognito.com'
cognito_token_key_url = 'https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_mX1uDv7na/.well-known/jwks.json'
code = None
state = None

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
    def do_GET(self):
        global code
        print(self.path)
        params = parse_qs(urlparse(self.path).query)
        if 'code' in params:
            code = params['code'][0]
            print(f"code: {code}")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if code:
            self.wfile.write(bytes(otherhtml, "UTF-8"))
        else:
            self.wfile.write(bytes(html, "UTF-8"))

    def do_POST(self):
        global code
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
        print("LoginWorker __init__() start")

        super().__init__()
        self.host_name = host_name
        self.port = port
        self.client_id = client_id
        self.cognito_uri = cognito_uri
        self.path = path
        self.launch_browser = launch_browser
        self.client = WebApplicationClient(client_id=self.client_id)
        self.web_server = None
        print("LoginWorker __init__() end")

        self.oauth_session = None

    def run(self):
        global code, state
        print("LoginWorker run() start")
        self.oauth_session = OAuth2Session(client=self.client,
                                           redirect_uri=f"http://{self.host_name}:{self.port}{self.path}")
        print(f"http://{self.host_name}:{self.port}{self.path}")
        authorization_url, state = self.oauth_session.authorization_url(f"{self.cognito_uri}/login")
        logger.info(f"{authorization_url}")
        print(f"{authorization_url}")
        if self.launch_browser:
            webbrowser.open(authorization_url)
        else:
            print(f"Please authorize rdp upload here: {authorization_url}")

        self.web_server = HTTPServer((self.host_name, self.port), TokenServer)
        logger.debug(f"Server starting http://{self.host_name}:{self.port}")
        print(f"Server starting http://{self.host_name}:{self.port}")
        while code is None:
            print("Handling")
            self.web_server.handle_request()

        self.web_server.server_close()
        print("After webserver close")
        print("LoginWorker run() end")

        logger.info("Configured access token and shutdown server")

    def get_session(self):
        return self.oauth_session


class UserInfo():
    def __init__(self, name, email, authorized=False, message=""):
        self.name = name
        self.email = email
        self.authorized = authorized
        self.message = message

    @classmethod
    def _get_jwt_encryption_pub_keys(self):
        response = requests.get('https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_mX1uDv7na/.well-known/jwks.json')
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            print(response.json())
            print(type(response.json()))
            return response.json()

    @classmethod
    def from_id_token(cls, id_token, access_token):
        jwt_object = JWT()
        data = cls._get_jwt_encryption_pub_keys()
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
        return cls(decoded['name'], decoded['email'], authorized=authorized, message=message)


class ReefCloudSession():
    def __init__(self, client_id, cognito_url):
        self.client_id = client_id
        self.cognito_url = cognito_url
        self.current_user = None
        self.is_logged_in = False



    def login(self):
        global code, state
        login_worker = LoginWorker(self.client_id, self.cognito_url)
        login_worker.start()
        login_worker.join()
        self.oauth2_session = login_worker.get_session()

        token_url = f'{cognito_uri}/oauth2/token'
        self.tokens = self.oauth2_session.fetch_token(token_url,
                                                      code=code,
                                                      state=state,
                                                      client_id=self.client_id,
                                                      include_client_id=True)
        self.id_token = self.tokens['id_token']
        self.access_token = self.tokens['access_token']
        self.current_user = UserInfo.from_id_token(self.id_token, self.access_token)
        self.is_logged_in = True
        # Set code to none so if the user clicks the login page a second time, the web server waits for the new code
        code = None
        return self.tokens

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
        return self.delete(url, **kwargs)
