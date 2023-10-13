import logging
import os

import simplekml
from reefscanner.basic_model.photo_csv_maker import track
from reefscanner.basic_model.survey import Survey
from shapely import Polygon, MultiPoint
import alphashape

from aims import utils

logger = logging.getLogger("")
def make_kml(survey: Survey, cots_waypoints):
    input_folder = survey.folder
    output_folder = utils.replace_last(survey.folder, "/reefscan/", "/reefscan_kml/")
    points = track(input_folder, False)
    os.makedirs(os.path.dirname(output_folder), exist_ok=True)
    kml_file_name = f"{output_folder}.kml"
    kml = simplekml.Kml()
    for point in points:
        kml.newpoint(coords=[(point[1], point[0])])
    kml.save(kml_file_name)

    if len(cots_waypoints) > 0:
        kml_file_name = f"{output_folder}-cots.kml"
        kml = simplekml.Kml()
        for point in cots_waypoints:
            kml.newpoint(coords=[(point[1], point[0])])
        kml.save(kml_file_name)

    points_for_poly = []
    for point in points:
        points_for_poly.append((point[1], point[0]))

    kml_file_name = f"{output_folder}-poly.kml"
    kml = simplekml.Kml()

    # polygon: Polygon = MultiPoint(points_for_poly).convex_hull
    # polygon = alphashape.alphashape(points_for_poly, alpha=0.5)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=0.6)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=0.7)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=0.8)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=0.9)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=1)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=1.2)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=1.4)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=1.6)
    # logger.info(len(polygon.exterior.coords))
    # polygon = alphashape.alphashape(points_for_poly, alpha=1.8)
    # logger.info(len(polygon.exterior.coords))
    try:
        polygon = alphashape.alphashape(points_for_poly, alpha=2)
        logger.info(len(polygon.exterior.coords))
        kml_poly = kml.newpolygon()
        kml_poly.outerboundaryis = polygon.exterior.coords
        kml.save(kml_file_name)
    except:
        pass



