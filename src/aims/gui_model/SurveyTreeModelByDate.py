import datetime
from operator import itemgetter

from pytz import timezone


class SurveyTreeModelByDate:
    def __init__(self, survey_data, local_tz):
        utc = timezone("UTC")
        dates={}
        for survey_id, survey in survey_data.items():
            try:
                seq_part = survey_id[16:]
                try:
                    start_date = survey.start_date
                    naive_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
                except:
                    date_part = survey_id[:15]
                    naive_date = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S")
                utc_date = utc.localize(naive_date)
                local_date = utc_date.astimezone(local_tz)
                survey.time_name = datetime.datetime.strftime(local_date, "%H:%M:%S") + " " + seq_part
                date_name = datetime.datetime.strftime(local_date, "%Y-%m-%d")
            except Exception as e:
                print(e)
                survey.time_name = survey_id
                date_name = "unknown date"

            if date_name in dates:
                dates[date_name].append(survey)
            else:
                dates[date_name] = [survey]

        dates = dict(sorted(dates.items()))
        # for date_name in dates.keys():
        #     dates[date_name] = sorted(dates[date_name], key=itemgetter('id'))

        self.first_level = dates

