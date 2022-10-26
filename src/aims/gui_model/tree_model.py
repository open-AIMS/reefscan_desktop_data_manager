from PyQt5.QtGui import QStandardItemModel

from aims.gui_model.SurveyTreeModel import SurveyTreeModel
from aims.ui.checked_tree_item import CheckTreeitem
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent
from aims import state


def make_tree_model(include_camera=True, include_local=True):
    tree_model = QStandardItemModel()

    if include_camera:
        camera_branch = make_branch(state.model.camera_surveys, 'Reefscan Camera', checkable=True)
        tree_model.appendRow(camera_branch)
    if include_local:
        local_branch = make_branch(state.model.surveys_data, 'Local Drive', checkable=False)
        tree_model.appendRow(local_branch)

    return tree_model


def make_branch(survey_data, name, checkable):
    survey_tree_model = SurveyTreeModel(survey_data)
    branch = CheckTreeitem(name, checkable)
    sites = survey_tree_model.sites
    for site in sites.keys():
        site_branch = CheckTreeitem(site, checkable)
        branch.appendRow(site_branch)

        surveys = sites[site]
        for survey in surveys:
            survey_id = survey["id"]
            if survey_id != "archive":
                try:
                    name = survey["friendly_name"]
                except:
                    name = None
                if name is None or name == "":
                    name = survey_id
                survey_branch = CheckTreeitem(name, checkable)
                survey_branch.setData(survey_id, Qt.UserRole)
                site_branch.appendRow(survey_branch)
    return branch
