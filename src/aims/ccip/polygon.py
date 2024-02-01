import datetime
from typing import List

from aims.ccip.cull import Cull
from aims.ccip.tow_reefscan_results import TowReefscanResults


class Polygon():
    def __init__(self, dict):
        if dict == {}:
            self.reef = "Between"
            self.polygon = "Between"
            self.name = "Between"
            self.start_time = None
            self.end_time = None
        else:
            self.reef = dict["Reef"]
            self.polygon = dict["Polygon"]
            self.name = f"U/N_{self.reef}_{self.polygon}"
            start_time_str = dict.get("Start Time")
            end_time_str = dict.get("End Time")

            self.start_time: datetime = datetime.datetime.strptime(start_time_str,
                                                                   "%d/%m/%Y %H:%M:%S") - datetime.timedelta(hours=10)
            self.end_time: datetime = datetime.datetime.strptime(end_time_str,
                                                                 "%d/%m/%Y %H:%M:%S") - datetime.timedelta(hours=10)


        self.total_cots_culled = None
        self.reefscan_results = TowReefscanResults()

    def add_cull_data(self, culls: List[Cull]):
        self.total_cots_culled =0
        for cull in culls:
            self.total_cots_culled += cull.cots

    def dict(self):
        return {"name": self.name,
                "reef": self.reef,
                "polygon": self.polygon,
                "cots_culled": self.total_cots_culled,
                "cots_reefscan_total": self.reefscan_results.total_cots,
                "cots_reefscan_probable": self.reefscan_results.probable_cots,
                "cots_reefscan_confirmed": self.reefscan_results.confirmed_cots,
                "scar_reefscan_total": self.reefscan_results.total_scars,
                "scar_reefscan_confirmed": self.reefscan_results.confirmed_scars,
                "hc_reefscan": self.reefscan_results.hc_cover()

                }

