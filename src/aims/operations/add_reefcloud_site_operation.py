from PyQt5.QtWidgets import QApplication
from reefscanner.basic_model.survey import Survey

from aims.operations.abstract_operation import AbstractOperation
from aims.operations.aims_status_dialog import AimsStatusDialog
from aims.state import state
from aims2.reefcloud2.reefcloud_utils import create_reefcloud_site

def create_reefcloud_site_with_progress(site_name, project_name, survey: Survey, aims_status_dialog: AimsStatusDialog):
    operation = AddReefcloudSiteOperation(site_name, project_name, survey)
    operation.update_interval = 1
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()
    aims_status_dialog.close()
    print (operation.site_id)
    return operation.site_id


class AddReefcloudSiteOperation(AbstractOperation):
    def __init__(self, project_name, site_name, survey: Survey):
        super().__init__()
        self.site_name = site_name
        self.project_name = project_name
        self.survey = survey
        self.site_id = None

    def _run(self):
        self.set_progress_label("Creating Site")
        self.site_id = create_reefcloud_site(self.project_name, self.site_name, self.survey.start_lat, self.survey.start_lon,
                                        self.survey.start_depth)
        state.load_reefcloud_sites()



