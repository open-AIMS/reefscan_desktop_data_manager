import logging
import shutil

from aims.operations.abstract_operation import AbstractOperation
from aims.state import state
from aims.sync.sync_from_hardware import SyncFromHardware
from aims2.operations2.camera_utils import get_kilo_bytes_used

logger = logging.getLogger("")


class SyncFromHardwareOperation(AbstractOperation):

    def __init__(self, hardware_folder, local_folder, backup_data_folder, surveys, camera_samba):
        super().__init__()
        self.sync = SyncFromHardware(self.progress_queue, hardware_folder, local_folder, backup_data_folder, camera_samba)
        self.surveys = surveys

    def _run(self):
        self.check_space(self.surveys)
        return self.sync.sync(survey_infos=self.surveys)

    def check_space(self, surveys):
        try:
            total_kilo_bytes_used = 0
            for survey in surveys:
                if survey['branch'] == self.tr("New Sequences"):
                    command = f'du -s /media/jetson/*/images/{survey["survey_id"]}'
                else:
                    command = f'du -s /media/jetson/*/images/archive/{survey["survey_id"]}'

                kilo_bytes_used = get_kilo_bytes_used(state.config.camera_ip, command)
                logger.info(self.tr("Bytes used: ") + f"{kilo_bytes_used}")
                total_kilo_bytes_used += kilo_bytes_used

            logger.info(self.tr("total Bytes used: ") + f"{total_kilo_bytes_used}")

            logger.info(state.primary_drive)
            logger.info(state.backup_drive)

            du = shutil.disk_usage(state.primary_drive)
        except Exception as e:
            logger.error(self, "Error calulating disk usage or space. ", exc_info=True)
            return

        not_enough_disk = self.tr("Not enough disk space available on the primary disk.")
        not_enough_disk_back = self.tr("Not enough disk space available on the backup disk.")
        required = self.tr("Selected sequences require")
        avaliable = self.tr("Space available on")
        _is_ = self.tr("is")

        if total_kilo_bytes_used > du.free * 1000:
            gb_used = total_kilo_bytes_used / 1000000
            free_gb = du.free / 1000000000

            message = f"""
                {not_enough_disk}\n
                {required} {gb_used:.2f Gb}
                {avaliable} {state.primary_drive} {_is_} {free_gb:.2f} Gb
                """
            raise Exception(message)

        if state.backup_drive is not None:
            if total_kilo_bytes_used > du.free * 1000:
                du = shutil.disk_usage(state.backup_drive)
                gb_used = total_kilo_bytes_used / 1000000
                free_gb = du.free / 1000000000
                message = f"""
                    {not_enough_disk_back}\n
                    {required} {gb_used:.2f Gb}
                    {avaliable} {state.primary_drive} {_is_} {free_gb:.2f} Gb
                    """
                raise Exception(message)

    def cancel(self):
        super().cancel()
        if not self.finished:
            logger.info("I will cancel")
            self.sync.cancel()
