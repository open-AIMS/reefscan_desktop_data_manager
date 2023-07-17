import json
import os

from reefscanner.basic_model.survey import Survey

from aims.state import state
import requests

surveys_folder = "surveys"


def check_reefcloud_metadata(surveys: list[Survey]):
    for survey in surveys:
        best_name = survey.best_name()

        if survey.reefcloud_project is None:
            raise Exception(f"Missing reefcloud project for {best_name}")

        project_ = survey.reefcloud_project
        if not state.config.valid_reefcloud_project(project_):
            raise Exception(f"Invalid reefcloud project {project_} for {best_name}")

        if survey.reefcloud_site is None:
            raise Exception(f"Missing reefcloud site for {best_name}")

        site_ = survey.reefcloud_site
        if not state.config.valid_reefcloud_site(site_, project_):
            raise Exception(f"Invalid reefcloud site {site_} for {best_name}")


def write_reefcloud_photos_json(survey_id, outputfile, selected_photo_infos):
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
    create_signed_url_url = f'{state.config.api_url}/upload'

    oauth2_session.check_refresh()
    full_file_name = f"{folder}/{file_name}"
    if os.path.isdir(full_file_name):
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


def update_reefcloud_projects(oauth2_session):
    oauth2_session.check_refresh()
    project_result = download_reefcloud_projects(oauth2_session)
    return project_result


def create_reefcloud_site(project_name, site_name, latitude, longitude, depth):
    print(project_name, site_name)
    oauth2_session = state.reefcloud_session
    oauth2_session.check_refresh()
    headers = {
        'Authorization': 'Bearer {}'.format(oauth2_session.id_token)
    }
    # url = state.config.projects_json_download_url
    url = f"{state.config.sites_json_download_url}?org={project_name}"
    data = {
        "locations": [
            {
                "name": site_name,
                "type": "Site",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        longitude,
                        latitude
                    ]
                },
                "properties": {
                    "reefZone": "crest",
                    "reefName": site_name,
                    "siteCode": site_name,
                    "depth": f"{depth}",
                    "country": "Australia"
                }
            }
        ]
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    if r.status_code >= 400:
        if "location_unique_by_name_and_organisation" in r.text:
            raise Exception(f"Site {site_name} already exists in reefcloud. Try 'Download Projects and Sites' on the reefcloud tab.")
        else:
            raise Exception(f"Error creating site {r.text}")

    print(r.text)
    new_sites = json.loads(r.text)
    update_reefcloud_sites(oauth2_session)
    return new_sites[0]["id"]

def update_reefcloud_sites(oauth2_session):
    oauth2_session.check_refresh()
    sites = {}
    site_count = 0
    for project in state.config.reefcloud_projects:
        sites[project] = download_reefcloud_sites_for_project(oauth2_session, project)
        site_count += len(sites[project])

    filename = state.config.config_folder + "/" + state.config.reefcloud_sites_filename
    with open(filename, "w") as write_file:
        json.dump(sites, write_file)
    return f"{site_count} sites downloaded"


def download_reefcloud_projects(oauth2_session):
    oauth2_session.check_refresh()
    print("In update_reefcloud_projects")
    print(oauth2_session.id_token)
    headers = {
        'Authorization': 'Bearer {}'.format(oauth2_session.id_token)
    }
    url = state.config.projects_json_download_url
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
    url = f"{state.config.sites_json_download_url}?org={reefcloud_project}"
    headers = {
        'Authorization': 'Bearer {}'.format(oauth2_session.id_token)
    }
    print(url)
    r = requests.get(url, headers=headers)
    print("response code " + str(r.status_code))

    if r.status_code < 400:
        # print(r.json())
        return r.json()
    else:
        raise Exception("Error downloading sites " + r.text)
