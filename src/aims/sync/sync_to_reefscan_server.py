import os
import shutil
from datetime import datetime

from aims.sync.synchroniser import Synchroniser


class SyncToReefScanServer(Synchroniser):

    def __init__(self, progress_queue):
        super().__init__(progress_queue)
        self.reefscan_folder = ""
        self.local_folder = ""
        self.s_project_file = ""
        self.s_sites_folder = ""
        self.s_surveys_folder = ""
        self.s_trips_folder = ""

        self.l_project_file = ""
        self.l_sites_folder = ""
        self.l_surveys_folder = ""
        self.l_trips_folder = ""

        self.archive_folder = ""

    def sync(self, local_folder, reefscan_folder):
        self.setup_folders(local_folder, reefscan_folder)

        #   Copy the project file from server to local. Overwrite.
        if os.path.exists(self.l_project_file):
            shutil.move(self.l_project_file, self.archive_folder)
        shutil.copyfile(self.s_project_file, self.l_project_file)

    #   Copy new sites from local to server

        if os.path.isdir(self.l_trips_folder):
            print("copying sites")
            shutil.copytree(self.l_sites_folder, self.s_sites_folder, dirs_exist_ok=True)

        # Copy all sites from server to local
        shutil.move(self.l_sites_folder, self.archive_folder)
        shutil.copytree(self.s_sites_folder, self.l_sites_folder)

    #   Copy all trips from local to server. Then Archive
        if os.path.isdir(self.l_trips_folder):
            print("copying trips")
            shutil.copytree(self.l_trips_folder, self.s_trips_folder, dirs_exist_ok=True)
            shutil.move(self.l_trips_folder, self.archive_folder)

    #   Copy all surveys from local to server. Then Archive
    #     cpt = sum([len(files) for r, d, files in os.walk(l_surveys_folder)])
    #     print(f"total files = {cpt}")
        if os.path.isdir(self.l_surveys_folder):
            print("copying surveys")
            self.copytree_parallel(self.l_surveys_folder, self.s_surveys_folder)
            if not self.cancelled:
                shutil.move(self.l_surveys_folder, self.archive_folder)
                message = f"Your data has been synchronised to the reefscan server. Data before sync is available here: {self.archive_folder}"
                detailed_message = """
                All surveys and photos have been copied to the server archived.\n
                All new sites have been copied to or from the server.
                New projects have been copied from the server. 
                """

                return (message, detailed_message)

        return ("operation not complete", "")

    def setup_folders(self, local_folder, reefscan_folder):
        self.reefscan_folder = reefscan_folder
        self.local_folder = local_folder
        if not os.path.isdir(self.reefscan_folder):
            raise Exception(f"Server not found at {self.reefscan_folder}")
        if not os.path.isdir(local_folder):
            os.mkdir(local_folder)
        dt_string = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        self.s_project_file = f'{self.reefscan_folder}/projects.json'
        self.s_sites_folder = f'{self.reefscan_folder}/sites'
        self.s_surveys_folder = f'{self.reefscan_folder}/images'
        self.s_trips_folder = f'{self.reefscan_folder}/trips'
        self.l_project_file = f'{self.local_folder}/projects.json'
        self.l_sites_folder = f'{self.local_folder}/sites'
        self.l_surveys_folder = f'{self.local_folder}/images'
        self.l_trips_folder = f'{self.local_folder}/trips'
        # if not os.path.exists(s_project_file):
        #     raise Exception (f"Project file does not exist on reefscan server. {s_project_file}")
        #
        # if not os.path.isdir(s_sites_folder):
        #     raise Exception (f"Sites folder does not exist on reefscan server. {s_sites_folder}")
        if not os.path.isdir(self.s_trips_folder):
            os.mkdir(self.s_trips_folder)
        if not os.path.isdir(self.s_surveys_folder):
            os.mkdir(self.s_surveys_folder)
        if not os.path.isdir(self.l_sites_folder):
            os.mkdir(self.l_sites_folder)
        if not os.path.isdir(self.l_surveys_folder):
            os.mkdir(self.l_surveys_folder)
        self.archive_folder = f'{self.local_folder}/archive'
        if not os.path.exists(self.archive_folder):
            os.mkdir(self.archive_folder)
        self.archive_folder = f'{self.archive_folder}/{dt_string}'
        os.mkdir(self.archive_folder)

    def pull_from_server(self, local_folder, reefscan_folder):
        self.setup_folders(local_folder, reefscan_folder)

        #   Copy the project file from server to local. Overwrite.
        if os.path.exists(self.l_project_file):
            shutil.move(self.l_project_file, self.archive_folder)
        shutil.copyfile(self.s_project_file, self.l_project_file)

        # Copy all sites from server to local
        shutil.move(self.l_sites_folder, self.archive_folder)
        shutil.copytree(self.s_sites_folder, self.l_sites_folder)

