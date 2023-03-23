from PyQt5.QtGui import QStandardItemModel

from aims.gui_model.SurveyTreeModelByDate import SurveyTreeModelByDate
from aims.ui.checked_tree_item import CheckTreeitem
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent
from aims import state


def make_tree_model(timezone, include_camera=True, include_local=True, include_archives=False, checkable=True):
    tree_model = QStandardItemModel()

    if include_camera:
        camera_branch = make_branch(state.model.camera_surveys, 'New Sequences', checkable=checkable, timezone=timezone)
        # if not include_local:
        #     for i in range(camera_branch.rowCount()):
        #         child_item = camera_branch.child(i)
        #         tree_model.appendRow(child_item)
        # else:
        tree_model.appendRow(camera_branch)
        if include_archives:
            archive_branch = make_branch(state.model.archived_surveys, 'Downloaded Sequences', checkable=checkable, timezone=timezone, grey=True)
            tree_model.appendRow(archive_branch)

    if include_local:
        local_branch = make_branch(state.model.surveys_data, 'Local Drive', checkable=checkable, timezone=timezone)
        # if not include_camera:
        #     for i in range(local_branch.rowCount()):
        #         child_item = local_branch.child(i)
        #         tree_model.appendRow(child_item)
        # else:
        tree_model.appendRow(local_branch)

    return tree_model


def make_branch(survey_data, top_level_name, checkable, timezone, grey=False):
    # survey_tree_model = SurveyTreeModelBySite(survey_data)
    survey_tree_model = SurveyTreeModelByDate(survey_data, timezone)
    branch = CheckTreeitem(top_level_name, checkable, grey)
    first_level_branches = survey_tree_model.first_level
    for first_level_branch_name in first_level_branches.keys():
        first_level_branch = CheckTreeitem(first_level_branch_name, checkable, grey)
        branch.appendRow(first_level_branch)

        surveys = first_level_branches[first_level_branch_name]
        for survey in surveys:
            survey_id = survey.id
            if survey_id != "archive":
                name = best_name(survey, survey_id)
                site = survey.site
                if site is None:
                    site = ""

                if survey.photos is not None:
                    photos = f"({survey.photos} photos)"
                else:
                    photos = ""

                survey_branch = CheckTreeitem(f"{name}-{site}{photos}", checkable, grey)
                survey_branch.setData({"survey_id": survey_id, "branch": top_level_name}, Qt.UserRole)
                first_level_branch.appendRow(survey_branch)
    return branch


def best_name(survey, survey_id):
    try:
        name = survey.friendly_name
    except:
        name = None

    if name is None or name == "":
        try:
            name = survey.time_name
        except:
            name = None

    if name is None or name == "":
        name = survey_id

    return name


def checked_surveys(model, parent: QModelIndex = QModelIndex()):
    surveys = []
    for r in range(model.rowCount(parent)):
        index: QModelIndex = model.index(r, 0, parent)
        model_item = model.itemFromIndex(index)
        if model_item.isCheckable() and model_item.checkState() == Qt.Checked:
            survey_id = index.data(Qt.UserRole)
            if survey_id is not None:
                surveys.append(survey_id)

        if model.hasChildren(index):
            child_surveys = checked_surveys(model, parent=index)
            surveys = surveys + child_surveys

    return surveys
