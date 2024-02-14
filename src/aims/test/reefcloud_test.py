from multiprocessing.pool import ThreadPool
from time import sleep

import requests

from aims.state import state
from aims2.reefcloud2.reefcloud_session import ReefCloudSession

state.config.set_dev(False)
state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)
threadPool = ThreadPool(16)
result = threadPool.apply_async(state.reefcloud_session.login)

while not result.ready():
    sleep(1)

state.reefcloud_session.check_refresh()
headers = {
    'Authorization': 'Bearer {}'.format(state.reefcloud_session.id_token)
}

url = "https://api.reefcloud.ai/reefcloud/api/user/access?min-level=WRITE"
r = requests.get(url, headers=headers)
print(url)
print(r.text)
print("")

url = "https://api.reefcloud.ai/reefcloud/api/organisation/list"
r = requests.get(url, headers=headers)
print(url)
print(r.text)
print("")
