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


def create_gpx_file(geojson_folder, gpx_folder, kml_filename, feature_name, coordinates):
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack(name=feature_name)
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    coords_list=[]
    for coord in coordinates.split():
        coord_list = coord.split(',')
        lon = float(coord_list[0])
        lat = float(coord_list[1])
        coord_list = [lon, lat]
        coords_list.append(coord_list)
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon))

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

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    geojson_filename = f"{geojson_folder}/{kml_filename}_{feature_name}.geojson"
    gpx_filename = f"{gpx_folder}/{kml_filename}_{feature_name}.gpx"


    with open(geojson_filename, 'w') as f:
        json.dump(geojson_data, f)

    with open(gpx_filename, 'w') as f:
        f.write(gpx.to_xml())


def create_points_gpx(geojson_folder, gpx_folder, start_points, filename, feature_suffix):
    gpx = gpxpy.gpx.GPX()
    features = []
    for lon, lat, name, short_name in start_points:
        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(latitude=float(lat), longitude=float(lon), name=f"{short_name}_{feature_suffix}"))
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
    geojson_filename = f"{geojson_folder}/{filename}.geojson"
    gpx_filename = f"{gpx_folder}/{filename}.gpx"
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(geojson_filename, 'w') as f:
        json.dump(geojson_data, f)

    with open(gpx_filename, 'w') as f:
        f.write(gpx.to_xml())



def make_geojson(kml_folder, geojson_folder, gpx_folder):
    start_points = []
    finish_points = []
    os.makedirs(geojson_folder, exist_ok=True)
    os.makedirs(gpx_folder, exist_ok=True)
    for filename in os.listdir(kml_folder):
        if filename.endswith('.kml'):
            kml_path = os.path.join(kml_folder, filename)
            linestrings = extract_linestrings_from_kml(kml_path)



            for feature_name, coordinates in linestrings:
                create_gpx_file(geojson_folder, gpx_folder, os.path.splitext(filename)[0], feature_name, coordinates)

                if coordinates:
                    coordinates_list = coordinates.split(' ')
                    lon, lat = coordinates_list[0].split(',')[:2]
                    start_points.append((lon, lat, f"{os.path.splitext(filename)[0]}_{feature_name}", feature_name))

                    lon, lat = coordinates_list[len(coordinates_list)-1].split(',')[:2]
                    finish_points.append((lon, lat, f"{os.path.splitext(filename)[0]}_{feature_name}", feature_name))

    if start_points:
        create_points_gpx(geojson_folder, gpx_folder, start_points, "00__first_points", "s")
        create_points_gpx(geojson_folder, gpx_folder, finish_points, "00__finish_points", "f")



