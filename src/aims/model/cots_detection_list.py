import json
import ntpath
import os
import pandas as pd

from PIL import Image
from PIL import UnidentifiedImageError
from PyQt5.QtCore import QObject
from reefscanner.basic_model.photo_csv_maker import make_photo_csv
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.model.cots_detection import CotsDetection
from aims.model.proportional_rectangle import ProportionalRectangle

# This stores all the information for COTS detections for a reefscan sequence
from aims.utils import read_json_file_support_samba

import logging
logger = logging.getLogger("")

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

    def read_eod_files(self, folder: str, samba: bool):
        if self.folder == folder:
            return False
        
        self.cots_detections_list = []
        self.image_rectangles_by_filename = {}

        self.folder = folder
        self.samba = samba
        self.read_eod_detection_files(folder)
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

    def read_eod_detection_files(self, folder: str):

        # Function to get the related folder containing the eod json files
        def get_eod_detections_dir(images_folder):
            parent_dir  = os.path.abspath(os.path.join(images_folder, '..'))
            eod_dir = f'{parent_dir}_eod_cots'
            seq_dir_name = os.path.basename(images_folder)
            eod_json_dir = os.path.join(eod_dir, seq_dir_name, 'final')
            return eod_json_dir

        # Function to normalize bounding box dimensions from 
        # pixel-based absolute to relative
        def normalize_box_dims(image_path, left, top, width, height):
            try:
                with Image.open(image_path) as img:
                    img_width, img_height = img.size
            except UnidentifiedImageError:
                logger.info(f'Unable to read {image_path}')
                img_width = 1
                img_height = 1
            return (float(left) / img_width,
                    float(top) / img_height,
                    float(width) / img_width,
                    float(height) / img_height)
        
        # Data structure for monitoring eod detections where one
        # can insert a detection with the same sequence id (annotation id). 
        # This data structure will perform the necessary checks and will
        # preserve the highest detection score if there are duplicates
        # Additionally it will accumulate the image filenames for each detection.
        class EodDetectionsDict():
            def __init__(self):
                self.reference_dict = {}

            def insert(self, cots_detection_item: CotsDetection, image_path):
                sequence_id = cots_detection_item.sequence_id
                current_images = []                
                if sequence_id not in self.reference_dict:
                    self.reference_dict[sequence_id] = cots_detection_item
                else:
                    current_images = self.reference_dict[sequence_id].images
                    old_detection = self.reference_dict[sequence_id]
                    if cots_detection_item.best_score > old_detection.best_score:
                        self.reference_dict[sequence_id] = cots_detection_item
                        
                if image_path not in current_images:
                    current_images.append(image_path)
                    self.reference_dict[sequence_id].images = current_images


            def extract_to_list(self):
                return [i for i in self.reference_dict.values()]


        detection_ref = EodDetectionsDict()
        self.cots_detections_list = []
        ops = get_file_ops(self.samba)

        # this will be an array of single row data frames
        # one for each image with cots
        cots_waypoint_dfs = []

        eod_cots_folder = get_eod_detections_dir(folder)

        if os.path.exists(eod_cots_folder):

            # Iterate through the json files in the eod cots folder
            for filename in ops.listdir(eod_cots_folder):
                file_path = f"{eod_cots_folder}/{filename}"

                # Check if the file is a JSON file
                if filename.endswith(".json") and os.path.isfile(file_path):
                    try:
                        # Load the JSON content from local disk or samba drive
                        json_data = read_json_file_support_samba(file_path, self.samba)

                        # Check if the file is an EOD COTS detection file based on keys
                        if 'frame_filename' and 'data' in json_data:

                            detections_list = json_data['data']['detections']

                            photo_file_name = ntpath.basename(json_data["frame_filename"])
                            photo_file_name_path = f"{self.folder}/{photo_file_name}"

                            for detection in detections_list:
                                class_id = 0
                                sequence_id = detection['annotation_id']
                                score = detection['score']
                                cots_detections_info = CotsDetection(sequence_id=sequence_id,
                                                                    best_class_id=class_id,
                                                                    best_score=score,
                                                                    images=[]
                                                                    )
                                detection_ref.insert(cots_detections_info, photo_file_name_path)

                            rectangles = []
                            for result in detections_list:
                                px_left = result["x"]
                                px_top = result["y"]
                                px_width = result["width"]
                                px_height = result["height"]
                                sequence_id = result["annotation_id"]
                                left, top, width, height = normalize_box_dims(photo_file_name_path, px_left, px_top, px_width, px_height)
                                rectangle = ProportionalRectangle(left, top, width, height, sequence_id)
                                rectangles.append(rectangle)
                            self.image_rectangles_by_filename[photo_file_name_path] = rectangles
                            # cots_waypoint_dfs.append(self.waypoint_by_filename(photo_file_name))

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {filename}: {e}")

        # Convert the EOD detection dictionary to list
        self.cots_detections_list = detection_ref.extract_to_list()
        
        for key in self.image_rectangles_by_filename:
            for rect in self.image_rectangles_by_filename[key]:
                rect: ProportionalRectangle
                logger.info(f'{key}')
                logger.info(f'{rect.sequence_id} {rect.top} {rect.left} {rect.width} {rect.height}')


        # # concat the array of waypoint data frames into one and convert to a list
        # if len(cots_waypoint_dfs) > 0:
        #     self.cots_waypoints = pd.concat(cots_waypoint_dfs).values.tolist()
        #     print(self.cots_waypoints)
        # else:
        #     self.cots_waypoints = []

    def image_list(self, detection_list):
        images = []
        for detection in detection_list:
            photo_file_name = ntpath.basename(detection["image"]["header"]["frame_id"])
            images.append(f"{self.folder}/{photo_file_name}")
        return images

# read all waypoint for the reefscan sequence into a pandas data frane
    def load_waypoints (self):
        if not self.samba:
            try:
                make_photo_csv(self.folder)
            except Exception as e:
                pass

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
