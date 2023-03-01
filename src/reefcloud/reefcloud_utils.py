import json
import os

import requests

api_url = 'https://xx6zbht7ue.execute-api.ap-southeast-2.amazonaws.com/prod/reefscan/api'

create_signed_url_url = f'{api_url}/upload'
surveys_folder = "surveys"


def write_reefcloud_photos_json (survey_name, outputfile, selected_photo_infos):
    reefcloud_infos = []
    for info in selected_photo_infos:
        reefcloud_info = {
            "s3-key": f"{surveys_folder}/{survey_name}/{info['filename']}",
            "depth": info["altitude"],
            "distance-from-camera": info["subject_distance"],
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "width": info["width"],
            "height": info["height"]
        }
        reefcloud_infos.append(reefcloud_info)

    with open(outputfile, "w") as text_file:
        text_file.write(json.dumps(selected_photo_infos))



def upload_file(oauth2_session, survey_name, folder, file_name):

    full_file_name = f"{folder}/{file_name}"
    if os.path.isdir (full_file_name):
        return
    size = os.path.getsize(full_file_name)
    if size == 0:
        return

    response = oauth2_session.put(create_signed_url_url,
                            data=json.dumps({"file_name": f"{surveys_folder}/{survey_name}/{file_name}"}))
    if not response.ok:
        raise Exception(f"Error uploading file {file_name}", response.text)

    if response.status_code == 208:
        # already uploaded
        print(f"{file_name} already uploaded")
        return

    signed_url = response.content.decode('utf-8')
    print(signed_url)
    # upload image
    headers = {
        "content-type": "application/unknown"
    }
    # headers = {
    #     "content-type": "image/jpeg"
    # }

    response = requests.put(signed_url, data=open(full_file_name, 'rb'), headers=headers)
    if not response.ok:
        raise Exception(f"Error uploading file {file_name}", response.text)


if __name__ == "__main__":
    upload_file("greg", "c:/temp/surfbee", "greg.xml")