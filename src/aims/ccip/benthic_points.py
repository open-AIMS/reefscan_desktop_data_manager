import csv
from operator import attrgetter
from typing import List, Dict

from aims.ccip.benthic_point import BenthicPoint


class BenthicPoints():
    def __init__(self, csv_file_name):
        self.points_by_photo: Dict[str, List[BenthicPoint]] = {}
        with open(csv_file_name, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                point = BenthicPoint(row)
                points = self.points_by_photo.get(point.photo)
                if points is None:
                    points = []
                points.append(point)
                self.points_by_photo[point.photo] = points


