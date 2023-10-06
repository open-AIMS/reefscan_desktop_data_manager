import json
import ntpath
import os

from PyQt5.QtCore import QObject

from aims.model.cots_detection import CotsDetection
from aims.model.proportional_rectangle import ProportionalRectangle

# This stores all the information for COTS detections for a reefscan sequence
class CotsDetectionList():
    def __init__(self):
        # detection list is an array of CotsDection
        # each element represents a sequence (or individual COTS tracked through many photos)
        self.cots_detections_list = []

        # image rectangles by file name contains the location of the COTS in the photos
        # for each image it has a list of rectangles of type ProportionalRectangle marking the location of the COTS
        self.image_rectangles_by_filename = {}
        self.folder = None

    # Read the real time cots detections from files
    # Returns true if the data is modified otherwise false
    def read_realtime_files(self, folder: str):
        # If the folder is the same as the one passed
        if self.folder == folder:
            return False
        self.folder = folder
        self.read_realtime_sequence_files(folder)
        self.read_realtime_image_files(folder)
        return True

    # Read the information from the cots_image_*.json files. Each file corresponds to a photo
    # and has the location of the COTS stored in the file as a rectangle (proprtional to the size of the photo)
    # This method populates image_rectangles_by_filename
    def read_realtime_image_files(self, folder: str):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            # Check if the file is a cots sequence JSON file
            if filename.startswith("cots_image_") and filename.endswith(".json") and os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    try:
                        # Load the JSON content
                        json_data = json.load(file)
                        photo_file_name = ntpath.basename(json_data["header"]["frame_id"])
                        photo_file_name = f"{self.folder}/{photo_file_name}"
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

                        self.image_rectangles_by_filename[photo_file_name] = rectangles


                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {filename}: {e}")

    # Read the information from the cots_sequence_*.json files. Each file corresponds to a COTS sequence
    # a COTS sequence represents an individual COTS which is tracked through one or more photos
    # This method populates cots_detections_list
    def read_realtime_sequence_files(self, folder: str):

        self.cots_detections_list = []

        # Iterate through all files in the folder
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            # Check if the file is a cots sequence JSON file
            if filename.startswith("cots_sequence_") and filename.endswith(".json") and os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    try:
                        # Load the JSON content
                        json_data = json.load(file)

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
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {filename}: {e}")

    def image_list(self, detection_list):
        images = []
        for detection in detection_list:
            photo_file_name = ntpath.basename(detection["image"]["header"]["frame_id"])
            images.append(f"{self.folder}/{photo_file_name}")
        return images
