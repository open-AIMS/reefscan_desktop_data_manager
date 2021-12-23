import logging
import os
import shutil
from datetime import datetime
import smbclient
from smbclient import path, shutil
from aims.samba import aims_shutil
from joblib import Parallel, delayed

from aims.sync.synchroniser import Synchroniser

logger = logging.getLogger(__name__)


class SyncFromHardware(Synchroniser):

    def __init__(self, progress_queue, hardware_folder, local_folder, backup_folder):
        super().__init__(progress_queue)
        self.hardware_folder = hardware_folder
        self.local_folder = local_folder
        self.backup_folder = backup_folder

    def sync(self, survey_ids):
        if not smbclient.path.isdir(self.hardware_folder):
            raise Exception(f"Hardware not found at {self.hardware_folder}")

        if not os.path.isdir(self.local_folder):
            os.makedirs(self.local_folder)

        h_surveys_folder = f'{self.hardware_folder}/images'

        if not smbclient.path.isdir(h_surveys_folder):
            raise Exception(f"Hardware surveys not found at {h_surveys_folder}")

        #   Copy all surveys from hardware to local. Then Archive
        # self.copytree_parallel(h_surveys_folder, l_surveys_folder)
        for survey_id in survey_ids:
            h_survey_folder = h_surveys_folder + "/" + survey_id
            self.copytree_parallel(h_survey_folder, survey_id)
            smbclient.rmdir(h_survey_folder)
            logger.info("surveys copied")

        message = f"Your data has been synchronised to the local storage. "
        detailed_message = """
        All photos have been copied to the local and backup folders.\n
        """
        return message, detailed_message

    def copytree_parallel(self, l_surveys_folder, s_surveys_folder):
        self.files_to_copy = []
        self.total_files = 0
        self.cancelled = False
        start = datetime.now()
        aims_shutil.copytree(l_surveys_folder, s_surveys_folder, dirs_exist_ok=True, copy_function=self.prepare_copy,
                        ignore=self._ignore_copy)
        finish = datetime.now()
        logger.warn(f'copy tree took {(finish - start).total_seconds()} seconds')
        self.total_files = len(self.files_to_copy)
        logger.warn(f"total files = {self.total_files}")
        self.progress_queue.set_progress_max(self.total_files)
        result = Parallel(n_jobs=1, require='sharedmem')(
            delayed(self.copy2_verbose)(src, dst) for src, dst in self.files_to_copy)

        # for src, dst in self.files_to_copy:
        #     self.copy2_verbose(src, dst)

        finish = datetime.now()
        logger.warn(f'copy took {(finish - start).total_seconds()} seconds')

    def copy2_verbose(self, src, dst):
        logger.debug(f"copy2 {src}")

        l_dst = f"{self.local_folder}/images/{dst}"
        b_dst = f"{self.backup_folder}/images/{dst}"

        if self.cancelled:
            print("cancelled")
        else:
            message = f'copying  {src}'
            self.progress_queue.set_progress_label(message)
            os.makedirs(os.path.dirname(l_dst), exist_ok=True)
            smbclient.shutil.copyfile(src, l_dst)
            os.makedirs(os.path.dirname(b_dst), exist_ok=True)
            shutil.copyfile(l_dst, b_dst)
            smbclient.remove(src)

        self.progress_queue.set_progress_value()
        # logger.info("produced " + src)

