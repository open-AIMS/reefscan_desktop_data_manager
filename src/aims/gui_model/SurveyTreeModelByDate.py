import datetime

from pytz import timezone


class SurveyTreeModelByDate:
    def __init__(self, survey_data, local_tz):
        utc = timezone("UTC")
        dates={}
        for survey_id, survey in survey_data.items():
            try:
                date_part = survey_id[:15]
                seq_part = survey_id[16:]
                naive_date = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S")
                utc_date = utc.localize(naive_date)
                local_date = utc_date.astimezone(local_tz)
                survey["time_name"] = datetime.datetime.strftime(local_date, "%H:%M:%S") + " " + seq_part
                date_name = datetime.datetime.strftime(local_date, "%Y-%m-%d")
            except:
                survey["time_name"] = survey_id
                date_name = "unknown date"

            if date_name in dates:
                dates[date_name].append(survey)
            else:
                dates[date_name] = [survey]

        self.first_level = dates

