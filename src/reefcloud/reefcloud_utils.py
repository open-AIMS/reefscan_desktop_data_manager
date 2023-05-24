import json
import os
from aims import state
import requests

api_url = 'https://dev.reefscan.api.aims.gov.au/reefscan/api'

create_signed_url_url = f'{api_url}/upload'
surveys_folder = "surveys"


def write_reefcloud_photos_json (survey_id, outputfile, selected_photo_infos):
    reefcloud_infos = []
    for info in selected_photo_infos:
        reefcloud_info = {
            "s3-key": f"{surveys_folder}/{survey_id}/{info['filename']}",
            "depth": info["altitude"],
            "distance-from-camera": info["subject_distance"],
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "width": info["width"],
            "height": info["height"],
            "time": info["date_taken"] + "Z"
        }
        reefcloud_infos.append(reefcloud_info)

    with open(outputfile, "w") as text_file:
        text_file.write(json.dumps(reefcloud_infos))


# Uses an oauth2_session to upload a file named file_name in residing in a folder specified in var named folder to S3.
# The destination within S3 is f"{surveys_folder}/{survey_id}/{file_name}

def upload_file(oauth2_session, survey_id, folder, file_name):
    oauth2_session.check_refresh()
    full_file_name = f"{folder}/{file_name}"
    if os.path.isdir (full_file_name):
        return
    size = os.path.getsize(full_file_name)
    if size == 0:
        return

    response = oauth2_session.put(create_signed_url_url,
                            data=json.dumps({"file_name": f"{surveys_folder}/{survey_id}/{file_name}"}))
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
'''
def update_reefcloud_projects(oauth2_session):
    # The real url will be something like https://api.dev.reefcloud.ai/reefcloud/api/organisation/list?org=REEFSCAN
    print("In update_reefcloud_projects")
    try:
        url = "https://api.dev.reefcloud.ai/reefcloud/api/user/access?min-level=WRITE"
        r = oauth2_session.get(url)
        print("response code " + str(r.status_code))
        if r.status_code == 200:
            filename = state.config.config_folder + "/" + state.config.reefcloud_projects_filename
            with open(filename, 'w') as f:
                f.write(r.text)
                f.close()
                return True
    except Exception as e:
        print(e)
        print(type(e))
    return False
'''


def update_reefcloud_projects(oauth2_session):
    oauth2_session.check_refresh()
    project_result = download_reefcloud_projects(oauth2_session)
    state.config.load_reefcloud_projects()
    return project_result


def update_reefcloud_sites(oauth2_session):
    oauth2_session.check_refresh()
    sites = {}
    site_count=0
    for project in state.config.reefcloud_projects:
        sites[project] = download_reefcloud_sites_for_project(oauth2_session, project)
        site_count += len(sites[project])

    filename = state.config.config_folder + "/" + state.config.reefcloud_sites_filename
    with open(filename, "w") as write_file:
        json.dump(sites, write_file)
    return f"{site_count} sites downloaded"


def download_reefcloud_projects(oauth2_session):
    # The real url will be something like https://api.dev.reefcloud.ai/reefcloud/api/organisation/list?org=REEFSCAN

    print("In update_reefcloud_projects")
    print(oauth2_session.id_token)
    headers = {
        'Authorization': 'Bearer {}'.format(oauth2_session.id_token)
    }
    # url = state.config.projects_json_download_url
    url = "https://api.dev.reefcloud.ai/reefcloud/api/user/access?min-level=WRITE"
    r = requests.get(url, headers=headers)
    print("response code " + str(r.status_code))
    if r.status_code < 400:
        projects_json = json.loads(r.text)
        project_count = 0
        for k, v in projects_json.items():
            project_count += len(v)
        filename = state.config.config_folder + "/" + state.config.reefcloud_projects_filename
        with open(filename, 'w') as f:
            f.write(r.text)
            f.close()

        return f"{project_count} projects downloaded"
    else:
        raise Exception("Error downloading projects " + r.text)


def download_reefcloud_sites_for_project(oauth2_session, reefcloud_project):
    print("entering download_reefcloud_sites_for_project " + reefcloud_project)
    url = state.config.sites_json_download_url
    url = f"https://api.dev.reefcloud.ai/reefcloud/api/locations?org={reefcloud_project}"
    headers = {
        'Authorization': 'Bearer {}'.format(oauth2_session.id_token)
    }
    r = requests.get(url, headers=headers)
    print("response code " + str(r.status_code))

    if r.status_code < 400:
        # print(r.json())
        return r.json()
    else:
        raise Exception("Error downloading sites " + r.text)
