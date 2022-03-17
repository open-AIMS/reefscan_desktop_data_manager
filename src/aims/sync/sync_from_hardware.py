import logging
import os
import shutil
from datetime import datetime
from aims.samba import aims_shutil
from joblib import Parallel, delayed
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.sync.synchroniser import Synchroniser

logger = logging.getLogger(__name__)


class SyncFromHardware(Synchroniser):

    def __init__(self, progress_queue, hardware_folder, local_folder, backup_folder, camera_samba):
        super().__init__(progress_queue)
        self.hardware_folder = hardware_folder
        self.local_folder = local_folder
        self.backup_folder = backup_folder
        self.camera_samba = camera_samba
        self.camera_os = get_file_ops(self.camera_samba)

    def sync(self, survey_ids):

        if not self.camera_os.isdir(self.hardware_folder):
            raise Exception(f"Hardware not found at {self.hardware_folder}")

        if not os.path.isdir(self.local_folder):
            os.makedirs(self.local_folder)

        h_surveys_folder = f'{self.hardware_folder}/images'

        if not self.camera_os.isdir(h_surveys_folder):
            raise Exception(f"Hardware surveys not found at {h_surveys_folder}")

        #   Copy all surveys from hardware to local. Then Archive
        # self.copytree_parallel(h_surveys_folder, l_surveys_folder)
        for survey_id in survey_ids:
            h_survey_folder = h_surveys_folder + "/" + survey_id
            l_survey_folder = self.local_folder + "/images/" + survey_id

            self.copytree_parallel(h_survey_folder, l_survey_folder)
            self.camera_os.rmdir(h_survey_folder)
            logger.info("surveys copied")

        # for survey_id in survey_ids:
        #     add_exif_from_csv()

        message = f"Your data has been synchronised to the local storage. "
        detailed_message = """
        All photos have been copied to the local and backup folders.\n
        """
        return message, detailed_message

    def copytree_parallel(self, from_folder, to_folder):
        self.files_to_copy = []
        self.total_files = 0
        self.cancelled = False
        start = datetime.now()
        if self.camera_samba:
            aims_shutil.copytree(from_folder, to_folder, dirs_exist_ok=True, copy_function=self.prepare_copy,
                             ignore=self._ignore_copy)
        else:
            shutil.copytree(from_folder, to_folder, dirs_exist_ok=True, copy_function=self.prepare_copy,
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

        l_dst = dst
        dst_last_part = dst[len(self.local_folder): ]

        b_dst = f"{self.backup_folder}/{dst_last_part}"

        if self.cancelled:
            print("cancelled")
        else:
            message = f'copying  {src}'
            self.progress_queue.set_progress_label(message)
            os.makedirs(os.path.dirname(l_dst), exist_ok=True)
            self.camera_os.copyfile(src, l_dst)
            os.makedirs(os.path.dirname(b_dst), exist_ok=True)
            shutil.copyfile(l_dst, b_dst)
            self.camera_os.remove(src)

        self.progress_queue.set_progress_value()
        # logger.info("produced " + src)

