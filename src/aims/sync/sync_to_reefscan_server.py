import os
import shutil
from datetime import datetime

reefscan_folder= "c:/aims/reef-scanner/SERVER"
def sync_to_reefscan_server(local_folder):
    if not os.path.isdir(reefscan_folder):
        raise Exception (f"Server not found at {reefscan_folder}")

    if not os.path.isdir(local_folder):
        os.mkdir(local_folder)

    dt_string = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    s_project_file = f'{reefscan_folder}/projects.json'
    s_sites_folder = f'{reefscan_folder}/sites'
    s_surveys_folder = f'{reefscan_folder}/surveys'
    s_trips_folder = f'{reefscan_folder}/trips'

    l_project_file = f'{local_folder}/projects.json'
    l_sites_folder = f'{local_folder}/sites'
    l_surveys_folder = f'{local_folder}/surveys'
    l_trips_folder = f'{local_folder}/trips'

    if not os.path.exists(s_project_file):
        raise Exception (f"Project file does not exist on reefscan server. {s_project_file}")

    if not os.path.isdir(s_sites_folder):
        raise Exception (f"Sites folder does not exist on reefscan server. {s_sites_folder}")

    if not os.path.isdir(s_trips_folder):
        os.mkdir(s_trips_folder)

    if not os.path.isdir(s_surveys_folder):
        os.mkdir(s_surveys_folder)

    if not os.path.isdir(l_sites_folder):
        os.mkdir(l_sites_folder)

    if not os.path.isdir(l_surveys_folder):
        os.mkdir(l_surveys_folder)

    archive_folder = f'{local_folder}/archive'
    if not os.path.exists(archive_folder):
        os.mkdir(archive_folder)

    archive_folder = f'{archive_folder}/{dt_string}'
    os.mkdir(archive_folder)

#   Copy the project file from server to local. Overwrite.
    if (os.path.exists(l_project_file)):
        shutil.move(l_project_file, archive_folder)
    shutil.copyfile(s_project_file, l_project_file)

#   Copy new sites from local to server
    shutil.copytree(l_sites_folder, s_sites_folder, dirs_exist_ok=True)

#   Copy all sites from server to local
    shutil.move(l_sites_folder, archive_folder)
    shutil.copytree(s_sites_folder, l_sites_folder)

#   Copy all trips from local to server. Then Archive
    shutil.copytree(l_trips_folder, s_trips_folder, dirs_exist_ok=True)
    shutil.move(l_trips_folder, archive_folder)

#   Copy all surveys from local to server. Then Archive
    shutil.copytree(l_surveys_folder, s_surveys_folder, dirs_exist_ok=True)
    shutil.move(l_surveys_folder, archive_folder)


    message = f"Your data has been synchronised to the reefscan data. Data before sync is available here: {archive_folder}"
    detailed_message = """
    All surveys and photos have been copied to the server archived.\n
    All new sites have been copied to or from the server.
    New projects have been copied from the server. 
    """
    return (message, detailed_message)

