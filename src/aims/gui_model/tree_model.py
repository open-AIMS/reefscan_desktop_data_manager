import logging

from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QMainWindow
from reefscanner.basic_model.survey import Survey

from aims.gui_model.SurveyTreeModelByDate import SurveyTreeModelByDate
from aims.ui.checked_tree_item import CheckTreeitem
from PyQt5.QtCore import QItemSelection, Qt, QModelIndex, QSize, QEvent
from aims.state import state

logger = logging.getLogger("")
class TreeModelMaker(QMainWindow):
    def __init__(self):
        super().__init__()

    def make_tree_model(self, timezone, include_camera=True, include_local=True, include_archives=False, checkable=True):
        tree_model = QStandardItemModel()

        if include_camera:
            camera_branch = self.make_branch(state.model.camera_surveys, self.tr('New Sequences'), checkable=checkable, timezone=timezone)
            # if not include_local:
            #     for i in range(camera_branch.rowCount()):
            #         child_item = camera_branch.child(i)
            #         tree_model.appendRow(child_item)
            # else:
            tree_model.appendRow(camera_branch)
            if include_archives:
                archive_branch = self.make_branch(state.model.archived_surveys, self.tr('Downloaded Sequences'), checkable=checkable, timezone=timezone, grey=True)
                tree_model.appendRow(archive_branch)

        if include_local:
            local_branch = self.make_branch(state.model.surveys_data, self.tr('Local Drive'), checkable=checkable, timezone=timezone)
            # if not include_camera:
            #     for i in range(local_branch.rowCount()):
            #         child_item = local_branch.child(i)
            #         tree_model.appendRow(child_item)
            # else:
            tree_model.appendRow(local_branch)

        return tree_model


    def make_branch(self, survey_data, top_level_name, checkable, timezone, grey=False):
        # survey_tree_model = SurveyTreeModelBySite(survey_data)
        survey_tree_model = SurveyTreeModelByDate(survey_data, timezone)
        branch = CheckTreeitem(top_level_name, checkable, grey)
        first_level_branches = survey_tree_model.first_level
        for first_level_branch_name in first_level_branches.keys():
            first_level_branch = CheckTreeitem(first_level_branch_name, checkable, grey)
            branch.appendRow(first_level_branch)

            surveys = first_level_branches[first_level_branch_name]
            surveys = sorted(surveys, key=lambda s: s.best_name())
            for survey in surveys:
                survey_id = survey.id
                if survey_id != "archive":
                    name = best_name(survey, survey_id)
                    site = survey.site
                    if site is None:
                        site = ""

                    __photos__ = self.tr("photos")
                    if survey.photos is not None:
                        photos = f"({survey.photos} {__photos__})"
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


def checked_survey_ids(model, parent: QModelIndex = QModelIndex()):
    if model is None:
        return []
    surveys = []
    for r in range(model.rowCount(parent)):
        index: QModelIndex = model.index(r, 0, parent)
        model_item = model.itemFromIndex(index)
        if model_item.isCheckable() and model_item.checkState() == Qt.Checked:
            survey_info = index.data(Qt.UserRole)
            if survey_info is not None:
                surveys.append(survey_info)

        if model.hasChildren(index):
            child_surveys = checked_survey_ids(model, parent=index)
            surveys = surveys + child_surveys

    return surveys


def checked_surveys(model) -> list[Survey]:
    survey_infos = checked_survey_ids(model)
    surveys = []
    for survey_info in survey_infos:
        survey_id = survey_info["survey_id"]
        survey = state.model.surveys_data[survey_id]
        surveys.append(survey)

    surveys = sorted(surveys, key=lambda s: s.best_name())
    return surveys

