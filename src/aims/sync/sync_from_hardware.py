import logging
import os
import shutil
from datetime import datetime


from aims.sync.synchroniser import Synchroniser

logger = logging.getLogger(__name__)

class SyncFromHardware(Synchroniser):

    def __init__(self, progress_queue):
        super().__init__(progress_queue)

    def sync(self, hardware_folder, local_folder):
        if not os.path.isdir(hardware_folder):
            raise Exception(f"Hardware not found at {hardware_folder}")

        if not os.path.isdir(local_folder):
            raise Exception(f"Local folder not found at {local_folder}")

        dt_string = datetime.now().strftime("%Y-%m-%dT%H%M%S")

        h_surveys_folder = f'{hardware_folder}/images'

        l_surveys_folder = f'{local_folder}/images'

        if not os.path.isdir(h_surveys_folder):
            raise Exception(f"Hardware surveys not found at {h_surveys_folder}")

        archive_folder = f'{hardware_folder}/archive'
        if not os.path.exists(archive_folder):
            os.mkdir(archive_folder)

        archive_folder = f'{archive_folder}/{dt_string}'
        os.mkdir(archive_folder)

        #   Copy all surveys from hardware to local. Then Archive
        self.copytree_parallel(h_surveys_folder, l_surveys_folder)
        logger.info("surveys copied")

        try:
            shutil.move(h_surveys_folder, archive_folder)
        except Exception as e:
            logger.info(f"error moving {h_surveys_folder}")
            logger.info(e)
            logger.info("retry")
            shutil.move(h_surveys_folder, f"{archive_folder}/take2")

        logger.info("surveys moved")

        message = f"Your data has been synchronised to the local storage. Data before sync is available here: {archive_folder}"
        detailed_message = """
        All photos have been copied to the local and archived.\n
        """
        return message, detailed_message
