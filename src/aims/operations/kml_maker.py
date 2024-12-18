import logging
import os

import simplekml
from reefscanner.basic_model.model_utils import replace_last
from reefscanner.basic_model.photo_csv_maker import track
from reefscanner.basic_model.survey import Survey

from aims import utils

logger = logging.getLogger("")

def make_kml2(filename, tracks, cots):
    kml = simplekml.Kml()
    cots_folder = kml.newfolder(name="cots")
    for cot in cots:
        pnt = cots_folder.newpoint(coords=[(cot[1], cot[0])])
        pnt.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'
        pnt.style.iconstyle.color = simplekml.Color.red

    tracks_folder = kml.newfolder(name="track")
    for track in tracks:
        pnt = tracks_folder.newpoint(coords=[(track[1], track[0])])
        pnt.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'
        pnt.style.iconstyle.color = simplekml.Color.gray

    kml.save(filename)



def make_kml(survey: Survey, cots_waypoints, minimum_cots_score, output_folder, depth=False):
    import alphashape
    input_folder = survey.camera_dirs[1]
    points = track(input_folder, False)
    # os.makedirs(output_folder, exist_ok=True)
    kml_file_name = f"{output_folder}/{survey.best_name()}.kml"
    kml = simplekml.Kml()
    for point in points:
        pnt = kml.newpoint(coords=[(point[1], point[0])])
        # TODO Perhaps we need a legend for this
        if depth:
            # pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
            if point[3] < 8000:
                pnt.style.iconstyle.color = simplekml.Color.red
            elif point[3] < 12000:
                pnt.style.iconstyle.color = simplekml.Color.yellow
            else:
                pnt.style.iconstyle.color = simplekml.Color.green

    kml.save(kml_file_name)

    if len(cots_waypoints) > 0:
        kml_file_name = f"{output_folder}/{survey.best_name()}-cots.kml"
        kml = simplekml.Kml()
        for point in cots_waypoints:
            pnt = kml.newpoint(coords=[(point[1], point[0])])
        kml.save(kml_file_name)

    points_for_poly = []
    for point in points:
        points_for_poly.append((point[1], point[0]))

    kml_file_name = f"{output_folder}/{survey.best_name()}-bounding-box.kml"
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
