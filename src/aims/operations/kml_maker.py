import os

import simplekml
from reefscanner.basic_model.photo_csv_maker import track
from reefscanner.basic_model.survey import Survey
from shapely import Polygon, MultiPoint
import alphashape


def make_kml(survey: Survey):
    folder = survey.folder
    points = track(folder, False)
    if os.path.isdir(folder):
        kml_file_name = f"{folder}.kml"
        kml = simplekml.Kml()
        for point in points:
            kml.newpoint(coords=[(point[1], point[0])])
        kml.save(kml_file_name)

        points_for_poly = []
        for point in points:
            points_for_poly.append((point[1], point[0]))

        kml_file_name = f"{folder}-poly.kml"
        kml = simplekml.Kml()

        # polygon: Polygon = MultiPoint(points_for_poly).convex_hull
        polygon = alphashape.alphashape(points_for_poly, alpha=0.5)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=0.6)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=0.7)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=0.8)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=0.9)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=1)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=1.2)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=1.4)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=1.6)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=1.8)
        print(len(polygon.exterior.coords))
        polygon = alphashape.alphashape(points_for_poly, alpha=2)
        print(len(polygon.exterior.coords))
        kml_poly = kml.newpolygon()
        kml_poly.outerboundaryis = polygon.exterior.coords
        kml.save(kml_file_name)


    print ("Aye")

