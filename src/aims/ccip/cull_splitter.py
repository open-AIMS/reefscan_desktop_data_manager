import datetime
import os
import shutil
from typing import List

from aims.ccip.benthic_point import BenthicPoint
from aims.ccip.benthic_points import BenthicPoints
from aims.ccip.culls import Culls
from aims.ccip.polygon import Polygon
from aims.ccip.polygons import Polygons
from aims.ccip.tow import Tow
from aims.ccip.tows import Tows
from aims.model.cots_detection import CotsDetection
from aims.model.cots_detection_list import CotsDetectionList
from aims.operations.inference_operation import inference_result_folder


class CullSplitter():
    def __init__(self, cull_folder, polygons_file):
        self.input_folder = None
        self.output_folder = None
        culls:Culls = Culls(cull_folder)
        self.polygons:Polygons = Polygons(polygons_file)

        self.polygons.add_cull_data(culls)

        self.detections_by_first_photo = {}
        self.between_poly = Polygon({})

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

        self.between_poly = Polygon({})
        self.polygons.first()


        photos = [name for name in os.listdir(self.input_folder) if name.lower().endswith(".jpg")]
        photos = sorted(photos)

        for photo in photos:
            polygon = self.copy_photo(photo)
            self.count_detections(polygon, photo)
            self.count_benthic_points (polygon, benthic_points.points_by_photo.get(photo))

    def count_benthic_points(self, polygon:Polygon, points:List[BenthicPoint]):
        if points is None:
            return
        for point in points:
            polygon.reefscan_results.reefscan_total_points += 1
            if point.group == "HC":
                polygon.reefscan_results.reefscan_hc_points += 1


    def count_detections(self, polygon: Polygon, photo):
        detections = self.detections_by_first_photo.get(photo)
        if polygon.reefscan_results.first_photo_time is None:
            polygon.reefscan_results.first_photo_time = photo
        polygon.reefscan_results.last_photo_time = photo

        if detections is not None:
            for detection in detections:
                if polygon is not None:
                    if detection.best_class_id == 0:
                        polygon.reefscan_results.total_cots += 1
                        if detection.best_score > 0.5:
                            polygon.reefscan_results.probable_cots += 1
                        if detection.confirmed:
                            polygon.reefscan_results.confirmed_cots += 1

                    if detection.best_class_id == 1:
                        polygon.reefscan_results.total_scars += 1
                        if detection.confirmed:
                            polygon.reefscan_results.confirmed_scars += 1

    def copy_photo(self, photo):
        date_str = photo[:15]
        date = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        # print(date)
        cur_poly:Polygon = self.polygons.cur()
        if (cur_poly is None) or (date < cur_poly.start_time):
            return self.between_poly

        if date < cur_poly.end_time:
            output_folder = f"{self.output_folder}/{cur_poly.name}"
            input_file = f"{self.input_folder}/{photo}"
            os.makedirs(output_folder, exist_ok=True)
            # shutil.copy2(input_file, output_folder)
            return cur_poly
        else:
            self.polygons.next()

            return(self.copy_photo(photo))

