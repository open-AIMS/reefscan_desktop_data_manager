import json
import ntpath
import os
import pandas as pd
from PyQt5.QtCore import QObject
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.model.cots_detection import CotsDetection
from aims.model.proportional_rectangle import ProportionalRectangle

# This stores all the information for COTS detections for a reefscan sequence
from aims.utils import read_json_file_support_samba


class CotsDetectionList():
    def __init__(self):
        # detection list is an array of CotsDection
        # each element represents a sequence (or individual COTS tracked through many photos)
        self.cots_detections_list = []

        # image rectangles by file name contains the location of the COTS in the photos
        # for each image it has a list of rectangles of type ProportionalRectangle marking the location of the COTS
        self.image_rectangles_by_filename = {}
        self.folder = None
        # we support showing this information for data that is not already downloaded
        # if it is coming directly from the camera samba is set to true
        self.samba = False
        # all waypoints are read into a pandas dataframe
        # and the ones that have COTS are added to a list in the format expected
        # by the HTML map creator
        self.waypoint_dataframe = None
        self.cots_waypoints = []

    # Read the real time cots detections from files
    # Returns true if the data is modified otherwise false
    def read_realtime_files(self, folder: str, samba: bool):
        # If the folder is the same as the one passed
        if self.folder == folder:
            return False

        self.cots_detections_list = []
        self.image_rectangles_by_filename = {}

        self.folder = folder
        self.samba = samba
        self.load_waypoints()
        self.read_realtime_sequence_files()
        self.read_realtime_image_files()
        return True

    # Read the information from the cots_image_*.json files. Each file corresponds to a photo
    # and has the location of the COTS stored in the file as a rectangle (proprtional to the size of the photo)
    # This method populates image_rectangles_by_filename
    # json files may be on the local disks or a samba drive
    def read_realtime_image_files(self):
        ops = get_file_ops(self.samba)
        # this will be an array of single row data frames
        # one for each image with cots
        cots_waypoint_dfs = []
        for filename in ops.listdir(self.folder):
            file_path = f"{self.folder}/{filename}"
            # Check if the file is a cots image JSON file
            if filename.startswith("cots_image_") and filename.endswith(".json") and ops.exists(file_path):
                try:
                    # Load the JSON content from local disk or samba drive
                    json_data = read_json_file_support_samba(file_path, self.samba)

                    photo_file_name = ntpath.basename(json_data["header"]["frame_id"])
                    photo_file_name_path = f"{self.folder}/{photo_file_name}"
                    results = json_data["results"]
                    rectangles = []
                    for result in results:
                        left = result["detection"]["left_x"]
                        top = result["detection"]["top_y"]
                        width = result["detection"]["width"]
                        height = result["detection"]["height"]
                        sequence_id = result["sequence_id"]
                        rectangle = ProportionalRectangle(left, top, width, height, sequence_id)
                        rectangles.append(rectangle)

                    self.image_rectangles_by_filename[photo_file_name_path] = rectangles
                    cots_waypoint_dfs.append(self.waypoint_by_filename(photo_file_name))
                except Exception as e:
                    print(f"Error decoding JSON in {filename}: {e}")
        # concat the array of waypoint data frames into one and convert to a list
        if len(cots_waypoint_dfs) > 0:
            self.cots_waypoints = pd.concat(cots_waypoint_dfs).values.tolist()
            print(self.cots_waypoints)
        else:
            self.cots_waypoints = []

    # Read the information from the cots_sequence_*.json files. Each file corresponds to a COTS sequence
    # a COTS sequence represents an individual COTS which is tracked through one or more photos
    # This method populates cots_detections_list
    # json files may be on the local disks or a samba drive
    def read_realtime_sequence_files(self):

        self.cots_detections_list = []
        ops = get_file_ops(self.samba)

        # Iterate through all files in the folder
        for filename in ops.listdir(self.folder):
            file_path = f"{self.folder}/{filename}"

            # Check if the file is a cots sequence JSON file
            if filename.startswith("cots_sequence_") and filename.endswith(".json") and ops.exists(file_path):
                try:
                    # Load the JSON content from local disk or samba drive
                    json_data = read_json_file_support_samba(file_path, self.samba)

                    best_detection = json_data['maximum_scores'][0]

                    best_class_id = best_detection['class_id']
                    best_score = best_detection['maximum_score']
                    sequence_id = json_data['sequence_id']
                    images = self.image_list(json_data["detection"])

                    cots_detections_info = CotsDetection(sequence_id=sequence_id,
                                                         best_class_id=best_class_id,
                                                         best_score=best_score,
                                                         images=images
                                                         )
                    self.cots_detections_list.append(cots_detections_info)
                except Exception as e:
                    print(f"Error decoding JSON in {filename}: {e}")

    def image_list(self, detection_list):
        images = []
        for detection in detection_list:
            photo_file_name = ntpath.basename(detection["image"]["header"]["frame_id"])
            images.append(f"{self.folder}/{photo_file_name}")
        return images

# read all waypoint for the reefscan sequence into a pandas data frane
    def load_waypoints (self):
        file_ops = get_file_ops(self.samba)
        csv_file_name = self.folder + "/photo_log.csv"
        if file_ops.exists(csv_file_name):
            with file_ops.open(csv_file_name) as file:
                df = pd.read_csv(file)
        else:
            raise Exception("No photo log found.")

        self.waypoint_dataframe = df[["latitude", "longitude", "filename_string"]]
        self.waypoint_dataframe.set_index (["filename_string"])

    def waypoint_by_filename(self, filename):
        waypoint_df = self.waypoint_dataframe[self.waypoint_dataframe["filename_string"] == filename]
        return waypoint_df
