import logging

from aims.operations.abstract_operation import AbstractOperation
from aims.sync.sync_from_hardware import SyncFromHardware

logger = logging.getLogger(__name__)


class SyncFromHardwareOperation(AbstractOperation):

    def __init__(self, hardware_folder, local_folder):
        super().__init__()
        self.hardware_folder = hardware_folder
        self.local_folder = local_folder
        self.sync = SyncFromHardware(self.progress_queue)

    def _run(self):
        return self.sync.sync(self.hardware_folder, self.local_folder)
