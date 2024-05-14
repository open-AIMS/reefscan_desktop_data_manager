import datetime
import logging
from operator import itemgetter

from pytz import timezone

from aims.utils import survey_id_parts

logger = logging.getLogger("")
class SurveyTreeModelByDate:
    def __init__(self, survey_data, local_tz):
        utc = timezone("UTC")
        devices={}
        for survey_id, survey in survey_data.items():
            survey_parts = survey_id_parts(survey_id)
            try:
                device = survey_parts["device_id"]
            except:
                device = "Unknown ReefScan"
            try:

                seq_part = survey_parts["seq"]
                try:
                    start_date = survey.start_date
                    naive_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
                except:
                    date_part = f"{survey_parts['date']}_{survey_parts['time']}"
                    naive_date = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S")
                utc_date = utc.localize(naive_date)
                local_date = utc_date.astimezone(local_tz)
                survey.time_name = datetime.datetime.strftime(local_date, "%H:%M:%S") + " " + seq_part
                date_name = datetime.datetime.strftime(local_date, "%Y-%m-%d")
            except Exception as e:
                logger.info(e)
                survey.time_name = survey_id
                date_name = "unknown date"

            if device not in devices:
                devices[device] = {"dates": {}}
            dates = devices[device]["dates"]

            if date_name in dates:
                dates[date_name].append(survey)
            else:
                dates[date_name] = [survey]

        for device in devices:
            devices[device]["dates"] = dict(sorted(devices[device]["dates"].items()))
        # for date_name in dates.keys():
        #     dates[date_name] = sorted(dates[date_name], key=itemgetter('id'))

        self.first_level = devices

