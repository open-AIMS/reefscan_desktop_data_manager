import json
import os

import requests


def upload_file(survey_name, folder, file_name):
    full_file_name = f"{folder}/{file_name}"
    if os.path.isdir (full_file_name):
        return
    size = os.path.getsize(full_file_name)
    if size == 0:
        return

    response = requests.put('https://zb3d39vc2m.execute-api.ap-southeast-2.amazonaws.com/prod/reefscan/api/upload2',
                            data=json.dumps({"file_name": f"surveys/{survey_name}/{file_name}"}))
    if not response.ok:
        raise Exception(f"Error uploading file {file_name}", response.text)

    if response.status_code == 208:
        # already uploaded
        print(f"{file_name} already uploaded")
        return

    signed_url = response.content.decode('utf-8')
    # upload image
    headers = {
        "content-type": "application/unknown"
    }

    response = requests.put(signed_url, data=open(full_file_name, 'rb'), headers=headers)
    if not response.ok:
        raise Exception(f"Error uploading file {file_name}", response.text)
