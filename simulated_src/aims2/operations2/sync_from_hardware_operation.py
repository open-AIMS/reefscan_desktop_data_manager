import logging

from aims.messages import messages
from aims.operations.abstract_operation import AbstractOperation
from aims.state import state

from aims2.operations2.count_to_three import count_to_three

logger = logging.getLogger("")


class SyncFromHardwareOperation(AbstractOperation):

    def __init__(self, hardware_folder, local_folder, backup_data_folder, surveys, camera_samba):
        super().__init__()
        self.surveys = surveys


    def _run(self):
        i=0
        for survey in self.surveys:
            i+=1
            survey_id = survey["survey_id"]

            try:
                friendly_name = state.model.camera_surveys[survey_id].friendly_name
            except:
                friendly_name = survey_id

            count_to_three(self.progress_queue, f"{messages.survey()} {friendly_name}. {i} {messages.of()} {len(self.surveys)}")
