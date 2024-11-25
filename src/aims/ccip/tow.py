import datetime

from aims.ccip.tow_reefscan_results import TowReefscanResults


class Tow():
    def __init__(self, dict):
        time_str = dict.get("SurveyTime")
        if time_str is None:
            self.name = "between tows"
            self.time = None
        else:
            time_str = time_str[:19]
            self.time:datetime = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
            self.name = datetime.datetime.strftime(self.time, "%Y-%m-%dT%H-%M-%S")


        self.cots:str = dict.get("CrownOfThornsStarfishCount")
        self.scar:str = dict.get("FeedingScarCountRangeDescription")
        self.hc:str = dict.get("HardCoralProportionRangeDescription")
        self.sc:str = dict.get("SoftCoralProportionRangeDescription")
        self.dc:str = dict.get("RecentlyDeadCoralProportionRangeDescription")
        self.reef = dict.get("ReefName")
        self.reef_time = dict.get("ReefAttributedTime")
        self.reefscan_results: TowReefscanResults = TowReefscanResults()



    def finish_time(self):
        return self.time + datetime.timedelta(minutes=2)

    def dict(self):
        return {
            "reef": self.reef,
            "reef_time": self.reef_time,
            "first_photo_time": self.reefscan_results.first_photo_time,
            "last_photo_time": self.reefscan_results.last_photo_time,
            "time": self.name,
            "cots_manta": self.cots,
            "scar_manta": self.scar,
            "cots_reefscan_total": self.reefscan_results.total_cots,
            "cots_reefscan_probable": self.reefscan_results.probable_cots,
            "cots_reefscan_confirmed": self.reefscan_results.confirmed_cots,
            "scar_reefscan_total": self.reefscan_results.total_scars,
            "scar_reefscan_confirmed": self.reefscan_results.confirmed_scars,
            "hc_manta": self.hc,
            "hc_reefscan": self.reefscan_results.hc_cover()

        }
