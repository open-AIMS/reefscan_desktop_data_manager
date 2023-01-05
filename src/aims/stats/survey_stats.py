import os
import pandas as pd

from aims import state


class SurveyStats:
    def __init__(self):
        self.photos = 0
        self.missing_ping_depth = 0
        self.missing_pressure_depth = 0
        self.missing_gps = 0

    def calculate(self, survey):
        folder = survey["image_folder"]
        csv_file_name = folder + "/photo_log.csv"
        if os.path.exists(csv_file_name):
            with open(csv_file_name, mode="r") as file:
                df = pd.read_csv(file)
            self.photos = len(df)
            no_lat = df[pd.to_numeric(df['latitude'], errors='coerce').isnull()]
            self.missing_gps = len(no_lat)
            try:
                no_ping = df[pd.to_numeric(df['ping_depth'], errors='coerce').isnull()]
                self.missing_ping_depth = len(no_ping)
            except:
                pass
            try:
                no_pressure = df[pd.to_numeric(df['pressure_depth'], errors='coerce').isnull()]
                self.missing_pressure_depth = len(no_pressure)
            except:
                pass

    def calculate_surveys(self, survey_ids):
        for survey_id in survey_ids:
            survey = state.model.surveys_data[survey_id]
            survey_stats = SurveyStats()
            survey_stats.calculate(survey)
            self.photos += survey_stats.photos
            self.missing_ping_depth += survey_stats.missing_ping_depth
            self.missing_pressure_depth += survey_stats.missing_pressure_depth
            self.missing_gps += survey_stats.missing_gps
