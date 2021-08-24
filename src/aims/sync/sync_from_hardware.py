import os
import shutil
from datetime import datetime


def sync_from_hardware(hardware_folder, local_folder):
    if not os.path.isdir(hardware_folder):
        raise Exception(f"Hardware not found at {hardware_folder}")

    if not os.path.isdir(local_folder):
        raise Exception(f"Local folder not found at {local_folder}")

    dt_string = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    h_surveys_folder = f'{hardware_folder}/surveys'

    l_surveys_folder = f'{local_folder}/surveys'

    if not os.path.isdir(h_surveys_folder):
        raise Exception(f"Hardware surveys not found at {h_surveys_folder}")

    archive_folder = f'{hardware_folder}/archive'
    if not os.path.exists(archive_folder):
        os.mkdir(archive_folder)

    archive_folder = f'{archive_folder}/{dt_string}'
    os.mkdir(archive_folder)

    #   Copy all surveys from hardware to local. Then Archive
    shutil.copytree(h_surveys_folder, l_surveys_folder, dirs_exist_ok=True)
    try:
        shutil.move(h_surveys_folder, archive_folder)
    except Exception as e:
        print (f"error moving {h_surveys_folder}")
        print (e)
        print ("retry")

        shutil.move(h_surveys_folder, f"{archive_folder}/take2")


    message = f"Your data has been synchronised to the local storage. Data before sync is available here: {archive_folder}"
    detailed_message = """
    All photos have been copied to the local and archived.\n
    """
    return (message, detailed_message)
