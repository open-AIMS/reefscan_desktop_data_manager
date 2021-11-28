from aims.gui_model.model import GuiModel


class SurveyTreeModel:
    def __init__(self, model: GuiModel, sites_lookup):
        self.sites = {}
        survey_data = model.surveys_data
        for survey in survey_data.values():

            site_id = survey["site"]
            if site_id is None or site_id == '':
                site_name = "__Not Assigned"
            else:
                site_name = sites_lookup[site_id]
            if site_name in self.sites:
                self.sites[site_name].append(survey["id"])
            else:
                self.sites[site_name] = [survey["id"]]






