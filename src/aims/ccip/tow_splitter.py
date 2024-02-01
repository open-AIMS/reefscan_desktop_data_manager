import datetime
import os
import shutil
from typing import List

from aims.ccip.benthic_point import BenthicPoint
from aims.ccip.benthic_points import BenthicPoints
from aims.ccip.tow import Tow
from aims.ccip.tows import Tows
from aims.model.cots_detection import CotsDetection
from aims.model.cots_detection_list import CotsDetectionList
from aims.operations.inference_operation import inference_result_folder


class TowSplitter():
    def __init__(self, tow_folder):
        self.tow_folder: str = tow_folder
        self.input_folder = None
        self.output_folder = None
        self.tows:Tows = Tows(self.tow_folder)
        self.detections_by_first_photo = {}
        self.between_tow = Tow({})

    def build_detections(self):
        self.detections_by_first_photo = {}
        cots_detection_list = CotsDetectionList()
        cots_detection_list.read_eod_files(self.input_folder, samba=False, use_cache=True)
        print(len(cots_detection_list.cots_detections_list))
        for d in cots_detection_list.cots_detections_list:
            detection: CotsDetection = d
            detections_for_photo = self.detections_by_first_photo.get(os.path.basename(detection.images[0]))
            if detections_for_photo is None:
                detections_for_photo = []
            detections_for_photo.append(detection)
            self.detections_by_first_photo[os.path.basename(detection.images[0])] = detections_for_photo

        print (len(self.detections_by_first_photo))

    def read_benthic_inferences(self) -> BenthicPoints:
        inference_folder = inference_result_folder(self.input_folder)
        csv_file = f"{inference_folder}/results.csv"
        points = BenthicPoints(csv_file)
        return points

    def split(self):
        self.build_detections()
        benthic_points = self.read_benthic_inferences()
        self.between_tow = Tow({})

        self.tows.first()


        photos = [name for name in os.listdir(self.input_folder) if name.lower().endswith(".jpg")]
        photos = sorted(photos)

        for photo in photos:
            tow = self.copy_photo(photo)
            self.count_detections(tow, photo)
            self.count_benthic_points (tow, benthic_points.points_by_photo.get(photo))

    def count_benthic_points(self, tow:Tow, points:List[BenthicPoint]):
        if points is None:
            return
        for point in points:
            tow.reefscan_results.reefscan_total_points += 1
            if point.group == "HC":
                tow.reefscan_results.reefscan_hc_points += 1

    def count_detections(self, tow, photo):
        detections = self.detections_by_first_photo.get(photo)
        if tow.reefscan_results.first_photo_time is None:
            tow.reefscan_results.first_photo_time = photo
        tow.reefscan_results.last_photo_time = photo

        if detections is not None:
            for detection in detections:
                if tow is not None:
                    if detection.best_class_id == 0:
                        tow.reefscan_results.total_cots += 1
                        if detection.best_score > 0.5:
                            tow.reefscan_results.probable_cots += 1
                        if detection.confirmed:
                            tow.reefscan_results.confirmed_cots += 1

                    if detection.best_class_id == 1:
                        tow.reefscan_results.total_scars += 1
                        if detection.confirmed:
                            tow.reefscan_results.confirmed_scars += 1

    def copy_photo(self, photo):
        date_str = photo[:15]
        date = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        # print(date)
        cur_tow = self.tows.cur()
        if (cur_tow is None) or (date < cur_tow.time):
            return self.between_tow

        if date < cur_tow.finish_time():
            output_folder = f"{self.output_folder}/{cur_tow.name}"
            input_file = f"{self.input_folder}/{photo}"
            os.makedirs(output_folder, exist_ok=True)
            # shutil.copy2(input_file, output_folder)
            return cur_tow

        else:
            self.tows.next()
            return(self.copy_photo(photo))

