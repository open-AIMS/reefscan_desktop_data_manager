
class SurveyTreeModel:
    def __init__(self, survey_data):
        self.sites = {}
        for survey in survey_data.values():
            site_name = None
            if "site" in survey:
                site_name = survey["site"]
            if site_name is None or site_name == '':
                site_name = "__Not Assigned"

            if site_name in self.sites:
                self.sites[site_name].append(survey["id"])
            else:
                self.sites[site_name] = [survey["id"]]

