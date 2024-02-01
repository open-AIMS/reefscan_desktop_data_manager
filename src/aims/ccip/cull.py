class Cull():
    def __init__(self, dict):
        self.name = dict["CullSiteName"]
        self.cots = int(dict["Cohort1"]) + int(dict["Cohort2"]) + int(dict["Cohort3"]) + int(dict["Cohort4"])