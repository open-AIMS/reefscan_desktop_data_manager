# These parameters control which detections are shown on the map page and also on the COTS photos page
# They can be set on both of these two pages
import os

from aims.model.cots_detection_list import CotsDetectionList
from aims.operations import load_data


class CotsDisplayParams:
    def __init__(self):
        super().__init__()
        self.eod = False
        self.only_show_confirmed = False
        self.camera = "cam_1"
        self.minimum_score = 0.5
        self.realtime_cots_detection_list = {"cam_1": CotsDetectionList(), "cam_2": CotsDetectionList()}
        self.eod_cots_detection_list = {"cam_1": CotsDetectionList(), "cam_2": CotsDetectionList()}
        self.by_class = "both"

    def cots_detection_list(self):
        if self.eod:
            return self.eod_cots_detection_list[self.camera]
        else:
            return self.realtime_cots_detection_list[self.camera]


    def read_data(self, aims_status_dialog, folder, samba):

        for camera, detection_list in self.realtime_cots_detection_list.items():
            camera_folder = f"{folder}/{camera}"
            if os.path.exists(camera_folder):
                detection_list.read_realtime_files(camera_folder, samba, use_cache=True)

        for camera, detection_list in self.eod_cots_detection_list.items():
            if samba:
                detection_list.has_data = False
            else:
                load_data.read_eod_detections(aims_status_dialog, f"{folder}/{camera}",
                                              detection_list)
