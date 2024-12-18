import logging
import os
import pandas as pd

from aims.state import state

logger = logging.getLogger("")
def greater(a, b):
    if a is None:
        return b

    if b is None:
        return a

    if a>b:
        return a

    return b


def smaller(a, b):
    if a is None:
        return b

    if b is None:
        return a

    if a < b:
        return a

    return b


class SurveyStats:
    def __init__(self):
        self.photos = 0
        self.photos_from_csv = 0
        self.missing_ping_depth = 0
        self.missing_pressure_depth = 0
        self.missing_gps = 0
        self.max_ping = None
        self.min_ping = None

    def calculate(self, survey):
        survey_dfs = []
        for (camera, folder) in survey.camera_dirs.items():
            self.photos = survey.photos
            csv_file_name = folder + "/photo_log.csv"
            if os.path.exists(csv_file_name):
                with open(csv_file_name, mode="r") as file:
                    df = pd.read_csv(file)
            survey_dfs.append(df)

        survey_df = pd.concat(survey_dfs)

        self.photos_from_csv = len(survey_df)
        no_lat = survey_df[pd.to_numeric(survey_df['latitude'], errors='coerce').isnull() | (pd.to_numeric(survey_df['latitude'], errors='coerce') == 0)]
        self.missing_gps = len(no_lat)
        try:
            ping_numeric = pd.to_numeric(survey_df['ping_depth'], errors='coerce')
            no_ping = survey_df[ping_numeric.isnull() | (ping_numeric < 0)]
            self.max_ping = round(ping_numeric.max()/1000, 1)
            self.min_ping = round(ping_numeric.min()/1000, 1)
            self.missing_ping_depth = len(no_ping)
        except:
            pass
        try:
            no_pressure = survey_df[pd.to_numeric(df['pressure_depth'], errors='coerce').isnull() | (pd.to_numeric(survey_df['pressure_depth'], errors='coerce')<0)]
            self.missing_pressure_depth = len(no_pressure)
        except:
            pass


    def calculate_surveys(self, survey_infos):
        self.photos_from_csv = 0
        self.photos = 0
        for survey_info in survey_infos:
            survey = state.model.surveys_data[survey_info["survey_id"]]
            survey_stats = SurveyStats()
            survey_stats.calculate(survey)
            self.photos_from_csv += survey_stats.photos_from_csv
            self.photos += survey_stats.photos
            self.missing_ping_depth += survey_stats.missing_ping_depth
            self.missing_pressure_depth += survey_stats.missing_pressure_depth
            self.missing_gps += survey_stats.missing_gps
            self.min_ping = smaller(self.min_ping, survey_stats.min_ping)
            self.max_ping = greater(self.max_ping, survey_stats.max_ping)
