from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
from oauthlib.oauth2 import WebApplicationClient, MobileApplicationClient, BackendApplicationClient, TokenExpiredError
from threading import Thread
from requests_oauthlib import OAuth2Session
import webbrowser
import logging
from urllib.parse import urlparse, parse_qs
# import typer
import os

logger = logging.getLogger(__name__)


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

id_token = None
access_token = None
class TokenServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global access_token, id_token
        print(self.path)
        params = parse_qs(urlparse(self.path).query)
        if 'code' in params:
            access_token = params['code'][0]
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if access_token:
            self.wfile.write(bytes(otherhtml, "UTF-8"))
        else:
            self.wfile.write(bytes(html, "UTF-8"))

    def do_POST(self):
        global access_token, id_token
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        access_token = form.getvalue("access_token")
        id_token = form.getvalue("id_token")
        print("POST request")
        print("FORM: {}".format(form))
        print(f"Access token: {access_token}")
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
        # self.client = MobileApplicationClient(client_id=self.client_id)
        self.client = WebApplicationClient(client_id=self.client_id)
        self.web_server = None
        print("LoginWorker __init__() end")

        self.oauth_session = None

    def run(self):
        global access_token, id_token
        print("LoginWorker run() start")
        self.oauth_session = OAuth2Session(client=self.client,
                                           redirect_uri=f"http://{self.host_name}:{self.port}{self.path}")
        print(f"http://{self.host_name}:{self.port}{self.path}")
        authorization_url, state = self.oauth_session.authorization_url(f"{self.cognito_uri}/login")
        logger.info(f"{authorization_url}")
        print(f"{authorization_url}")
        if self.launch_browser:
            print("launcher start")
            webbrowser.open(authorization_url)
            command = f"\\\"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe\\\" \\\"{authorization_url}\\\""
            print(command)
            #os.system(command)
            #typer.launch(authorization_url, locate=True)
            print("launcher end")

        else:
            print(f"Please authorize rdp upload here: {authorization_url}")

        self.web_server = HTTPServer((self.host_name, self.port), TokenServer)
        logger.debug(f"Server starting http://{self.host_name}:{self.port}")
        print(f"Server starting http://{self.host_name}:{self.port}")
        while access_token is None:
            print("Henadling")
            self.web_server.handle_request()

        self.web_server.server_close()
        print("After webserver close")
        self.oauth_session.access_token = id_token
        print("LoginWorker run() end")

        logger.info("Configured access token and shutdown server")

    def get_session(self):
        return self.oauth_session

def bens_login(client_id, cognito_uri):
    print("Start bens_login")
    global access_token, id_token
    login_worker = LoginWorker(client_id, cognito_uri)
    login_worker.start()
    login_worker.join()

    oauth_session = OAuth2Session(client=login_worker.client, token=id_token)
    print("end bens login")
    return access_token # Or id_token?






