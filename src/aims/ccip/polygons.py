import csv
import os
from typing import List

from reefscanner.basic_model.json_utils import read_json_file

from aims.ccip.culls import Culls
from aims.ccip.polygon import Polygon



class Polygons():
    def __init__(self, polygon_file):
        self.polygons:List[Polygon] = []
        self.read_csv_file(polygon_file)

        self.polygons = sorted(self.polygons, key=lambda d: d.start_time)
        self.cur_index: int = 0


    def add_cull_data(self, culls: Culls):
        for polygon in self.polygons:
            culls_for_poly = culls.culls.get(polygon.name)
            if culls_for_poly is not None:
                polygon.add_cull_data(culls_for_poly)


    def read_csv_file(self, file):
        self.polygons = []
        with open(file, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                polygon = Polygon(row)
                self.polygons.append(polygon)

    def first(self):
        self.cur_index = 0
        return self.cur()

    def cur(self):
        if self.cur_index >= len(self.polygons):
            return None
        else:
            return self.polygons[self.cur_index]

    def next(self):
        self.cur_index+=1
        return self.cur()

    def dicts(self):
        dicts = []
        for polygon in self.polygons:
            dicts.append(polygon.dict())
        return dicts
