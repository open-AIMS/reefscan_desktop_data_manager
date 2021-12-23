
class SurveyTreeModel:
    def __init__(self, survey_data, sites_lookup):
        self.sites = {}
        for survey in survey_data.values():

            site_id = survey["site"]
            if site_id is None or site_id == '':
                site_name = "__Not Assigned"
            elif site_id in sites_lookup:
                site_name = sites_lookup[site_id]
            else:
                site_name = "__Not Assigned"

            if site_name in self.sites:
                self.sites[site_name].append(survey["id"])
            else:
                self.sites[site_name] = [survey["id"]]

