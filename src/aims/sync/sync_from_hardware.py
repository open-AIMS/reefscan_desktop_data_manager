import logging
import os
import shutil
import traceback
from datetime import datetime

from reefscanner.basic_model.json_utils import read_json_file
from smbclient._io import SMBDirectoryIO
from smbprotocol.file_info import FileInformationClass

from aims.messages import messages
from aims.state import state
from aims.samba import aims_shutil
from joblib import Parallel, delayed
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.sync.synchroniser import Synchroniser

logger = logging.getLogger("")


class SyncFromHardware(Synchroniser):

    def __init__(self, progress_queue, hardware_folder, local_folder, backup_folder, camera_samba):
        super().__init__(progress_queue)
        self.hardware_folder = hardware_folder
        self.local_folder = local_folder
        self.backup_folder = backup_folder
        self.backup = state.config.backup

        self.camera_samba = camera_samba
        self.camera_os = get_file_ops(self.camera_samba)
        self.folder_message = ""
        self.cancelled = False

    def sync(self, survey_infos):
        if not self.camera_os.isdir(self.hardware_folder):
            message = self.tr("Hardware not found at")
            raise Exception(f"{message} {self.hardware_folder}")

        if not os.path.isdir(self.local_folder):
            os.makedirs(self.local_folder)

        h_surveys_folder = f'{self.hardware_folder}'
        l_surveys_folder = self.local_folder
        archive_folder = h_surveys_folder + "/archive"
        try:
            self.camera_os.mkdir(archive_folder)
        except:
            pass

        if not self.camera_os.isdir(h_surveys_folder):
            message = self.tr("Hardware surveys not found at")
            raise Exception(f"{message} {h_surveys_folder}")

        #   Copy all surveys from hardware to local. Then Archive
        # self.copytree_parallel(h_surveys_folder, l_surveys_folder)
        tot_surveys = len(survey_infos)
        i=0
        for survey_info in survey_infos:
            survey_id = survey_info["survey_id"]
            already_archived = (survey_info["branch"] == self.tr("Downloaded Sequences"))
            try:
                friendly_name = state.model.camera_surveys[survey_id].friendly_name
            except:
                friendly_name = survey_id

            if not self.cancelled:
                i += 1
                self.progress_queue.reset()
                self.folder_message = f"{messages.survey()} {friendly_name}. {i} {messages.of()} {tot_surveys}"
                if already_archived:
                    h_survey_folder = archive_folder + "/" + survey_id
                else:
                    h_survey_folder = h_surveys_folder + "/" + survey_id

                survey_id_after_2020 = self.after_2020(survey_id, h_survey_folder)
                l_survey_folder = self.find_local_survey_folder(survey_id_after_2020)

                self.copytree_parallel(h_survey_folder, l_survey_folder)
                try:
                    self.camera_os.rmdir(h_survey_folder)
                except:
                    logger.warn(f"Cannot remove folder {h_survey_folder}")

                logger.info("surveys copied")

        # for survey_id in survey_ids:
        #     add_exif_from_csv()

        message = self.tr("Your data has been synchronised to the local storage. ")
        detailed_message = self.tr("All photos have been copied to the local and backup folders.")
        return message, detailed_message + "\n"

    def find_local_survey_folder(self, survey_id):
        for root, dirs, files in os.walk(self.local_folder):
            for dir in dirs:
                full_dir = f"{root}/{dir}".replace("\\", "/")
                survey_json_path = f"{full_dir}/survey.json"
                if os.path.exists(survey_json_path):
                    survey = read_json_file(survey_json_path)
                    if "id" in survey and survey["id"] == survey_id:
                        return f"{root}/{dir}"

        return self.local_folder + "/" + survey_id

    def copytree_parallel(self, from_folder, to_folder):
        self.files_to_copy = []
        self.total_files = 0

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

        if self.files_to_copy is not None:
            files = sorted(self.files_to_copy, key=lambda tup: tup[0])
            # result = Parallel(n_jobs=10, require='sharedmem')(
            #     delayed(self.copy2_verbose)(src, dst) for src, dst in files)
            for src, dst in files:
                self.copy2_verbose(src, dst)

        finish = datetime.now()
        logger.warn(f'copy took {(finish - start).total_seconds()} seconds')

    def copy2_verbose(self, src, dst):
        logger.debug(f"copy2 {src}")

        already_archived = "archive" in src

        l_dst = dst
        dst_last_part = dst[len(self.local_folder): ].replace("\\", "/")
        src_last_part = src[len(self.hardware_folder): ].replace("\\", "/")

        a_dst = f"{self.hardware_folder}/archive/{src_last_part}"

        if self.cancelled:
            logger.debug("cancelled")
        else:
            message = f'{messages.copying()}  {src}'
            logger.debug(message)
            try:
                if os.path.exists(l_dst) and not src.endswith("survey.json"):
                    message = f'{messages.skipping()} {src}'
                    # logger.info(message)
                    self.set_progress_label(message)
                else:
                    logger.debug(f"will copy {src}")
                    os.makedirs(os.path.dirname(l_dst), exist_ok=True)
                    self.camera_os.copyfile(src, l_dst)

                if self.backup:
                    b_dst = f"{self.backup_folder}/{dst_last_part}"
                    if os.path.exists(b_dst) and not src.endswith("survey.json"):
                        message = f'{messages.skipping()} {src}'
                    else:
                        logger.debug(f"will copy backup {src}")
                        os.makedirs(os.path.dirname(b_dst), exist_ok=True)
                        shutil.copyfile(l_dst, b_dst)

                if not already_archived:
                    archive_dir = os.path.dirname(a_dst)
                    if not self.camera_os.exists(archive_dir):
                        self.camera_os.mkdir(archive_dir)

                    if self.camera_os.exists(a_dst):
                        self.camera_os.remove(src)
                    else:
                        self.camera_os.move(src, a_dst)

                self.set_progress_label(message)
            except Exception as e:
                print (f"there is an exception. {e}")
                traceback.print_exception(e)
                raise e

        self.progress_queue.set_progress_value()
        # logger.info("produced " + src)

    def set_progress_label(self, message):
        self.progress_queue.set_progress_label(f"{self.folder_message}\n{message}")

    def after_2020(self, survey_id, camera_folder):
        if survey_id > "2020":
            return survey_id

        first_good_photo = self.find_first_photo_after_2020(camera_folder)
        if first_good_photo is None:
            return survey_id

        try:
            date_part = first_good_photo[:15]
            return date_part + survey_id[15:]
        except:
            return survey_id

    def find_first_photo_after_2020(self, folder):
        files = self.camera_os.listdir(folder)
        files.sort()
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".jpeg"):
                if file > "2020":
                    return file
        return None