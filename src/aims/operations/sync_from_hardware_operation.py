import logging

from aims.operations.abstract_operation import AbstractOperation
from aims.sync.sync_from_hardware import SyncFromHardware

logger = logging.getLogger("")


class SyncFromHardwareOperation(AbstractOperation):

    def __init__(self, hardware_folder, local_folder, backup_data_folder, surveys, camera_samba):
        super().__init__()
        self.sync = SyncFromHardware(self.progress_queue, hardware_folder, local_folder, backup_data_folder, camera_samba)
        self.surveys = surveys

    def _run(self):
        return self.sync.sync(survey_infos=self.surveys)
