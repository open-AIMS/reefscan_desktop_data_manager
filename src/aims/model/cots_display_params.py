# These parameters control which detections are shown on the map page and also on the COTS photos page
# They can be set on both of these two pages
from aims.model.cots_detection_list import CotsDetectionList


class CotsDisplayParams:
    def __init__(self):
        self.init()

    def init(self):
        self.eod = False
        self.only_show_confirmed = False
        self.minimum_score = 0.5
        self.realtime_cots_detection_list = CotsDetectionList()
        self.eod_cots_detection_list = CotsDetectionList()

    def cots_detection_list(self):
        if self.eod:
            return self.eod_cots_detection_list
        else:
            return self.realtime_cots_detection_list


    def read_data(self, folder, samba):

        self.realtime_cots_detection_list.read_realtime_files(folder, samba, use_cache=True)
        if samba:
            self.eod_cots_detection_list.has_data = False
        else:
            self.eod_cots_detection_list.read_eod_files(folder, samba, use_cache=True)