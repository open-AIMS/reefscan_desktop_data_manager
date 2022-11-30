from PyQt5.QtGui import QStandardItemModel

from aims.gui_model.SurveyTreeModelByDate import SurveyTreeModelByDate
from aims.gui_model.SurveyTreeModelBySite import SurveyTreeModelBySite
from aims.ui.checked_tree_item import CheckTreeitem
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent
from aims import state


def make_tree_model(timezone, include_camera=True, include_local=True, checkable=True):
    tree_model = QStandardItemModel()

    if include_camera:
        camera_branch = make_branch(state.model.camera_surveys, 'Reefscan Camera', checkable=True, timezone=timezone)
        # if not include_local:
        #     for i in range(camera_branch.rowCount()):
        #         child_item = camera_branch.child(i)
        #         tree_model.appendRow(child_item)
        # else:
        tree_model.appendRow(camera_branch)
    if include_local:
        local_branch = make_branch(state.model.surveys_data, 'Local Drive', checkable=False, timezone=timezone)
        # if not include_camera:
        #     for i in range(local_branch.rowCount()):
        #         child_item = local_branch.child(i)
        #         tree_model.appendRow(child_item)
        # else:
        tree_model.appendRow(local_branch)

    return tree_model


def make_branch(survey_data, name, checkable, timezone):
    # survey_tree_model = SurveyTreeModelBySite(survey_data)
    survey_tree_model = SurveyTreeModelByDate(survey_data, timezone)
    branch = CheckTreeitem(name, checkable)
    first_level_branches = survey_tree_model.first_level
    for first_level_branch_name in first_level_branches.keys():
        first_level_branch = CheckTreeitem(first_level_branch_name, checkable)
        branch.appendRow(first_level_branch)

        surveys = first_level_branches[first_level_branch_name]
        for survey in surveys:
            survey_id = survey["id"]
            if survey_id != "archive":
                name = best_name(survey, survey_id)
                survey_branch = CheckTreeitem(name, checkable)
                survey_branch.setData(survey_id, Qt.UserRole)
                first_level_branch.appendRow(survey_branch)
    return branch


def best_name(survey, survey_id):
    try:
        name = survey["friendly_name"]
    except:
        name = None

    if name is None or name == "":
        try:
            name = survey["time_name"]
        except:
            name = None

    if name is None or name == "":
        name = survey_id
    return name
