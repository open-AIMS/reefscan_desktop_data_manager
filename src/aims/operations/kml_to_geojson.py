import json
import os
import xml.etree.ElementTree as ET
import gpxpy
import gpxpy.gpx

import logging
logger = logging.getLogger("")
def extract_linestrings_from_kml(kml_path):
    linestrings = []
    tree = ET.parse(kml_path)
    root = tree.getroot()

    for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        name = placemark.find(".//{http://www.opengis.net/kml/2.2}name").text
        linestring_element = placemark.find(
            ".//{http://www.opengis.net/kml/2.2}LineString/{http://www.opengis.net/kml/2.2}coordinates")

        if linestring_element is not None:
            coordinates = linestring_element.text.strip()
            linestrings.append((name, coordinates))

    return linestrings


def create_gpx_file(output_folder, kml_filename, feature_name, many, coordinates):
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    coords_list=[]
    for coord in coordinates.split():
        coord_list = coord.split(',')
        coord_list = [float(coord_list[0]), float(coord_list[1])]
        coords_list.append(coord_list)
    path_feature = {
        "type": "Feature",
        "properties": {
            "name": feature_name
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords_list
        }
    }
    features = [path_feature]

        # features.append(path_feature)
        # lon, lat = coord.split(',')[:2]
        # gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=float(lat), longitude=float(lon)))

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    if many:
        gpx_filename = f"{output_folder}/{kml_filename}_{feature_name}.geojson"
    else:
        gpx_filename = f"{output_folder}/{kml_filename}.geojson"


    with open(gpx_filename, 'w') as f:
        json.dump(geojson_data, f)

        # f.write(gpx.to_xml())


def create_start_points_gpx(output_folder, start_points):
    # gpx = gpxpy.gpx.GPX()
    features = []
    for lon, lat, name in start_points:
        # gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(latitude=float(lat), longitude=float(lon), name=name))
        point_feature = {
            "type": "Feature",
            "properties": {
                "name": name
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            }
        }
        features.append(point_feature)
    gpx_filename = f"{output_folder}/00__first_points.geojson"
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(gpx_filename, 'w') as f:
        json.dump(geojson_data, f)




def make_geojson(kml_folder, output_folder):
    start_points = []
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(kml_folder):
        if filename.endswith('.kml'):
            kml_path = os.path.join(kml_folder, filename)
            linestrings = extract_linestrings_from_kml(kml_path)

            many = len(linestrings) > 1

            for feature_name, coordinates in linestrings:
                create_gpx_file(output_folder, os.path.splitext(filename)[0], feature_name, many, coordinates)

                if coordinates:
                    lon, lat = coordinates.split(' ')[0].split(',')[:2]
                    start_points.append((lon, lat, f"{os.path.splitext(filename)[0]}_{feature_name}"))
    if start_points:
        create_start_points_gpx(output_folder, start_points)



