import json
import ntpath
import os
import pandas as pd

from PIL import Image
from PIL import UnidentifiedImageError
from reefscanner.basic_model.json_utils import read_json_file
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.model.cots_detection import CotsDetection, serialize_cots_detection_list, de_serialize_cots_detection_list
from aims.model.proportional_rectangle import ProportionalRectangle, serialize_proportional_rectangle_lookup, \
    de_serialize_proportional_rectangle_lookup

# This stores all the information for COTS detections for a reefscan sequence
from aims.utils import read_json_file_support_samba, replace_last, read_json_file, write_json_file

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
        self.has_data = False
        self.eod_detections_folder = None
        self.eod=False

# serialize and deserialize for efficiency. Reading the original data files can be quite slow especially for eod files
# we deliberately do not serialize the waypoint_data_frame because it is only used when from original files
# also do not cache folder or samba because we need to already know that before de-serializing
# don't cache if it is still on the camera
    def serialize(self):
        if self.samba:
            return
        cache_file = self.cache_file()
        dict = {"cots_detections_list": serialize_cots_detection_list(self.cots_detections_list),
                "image_rectangles_by_filename": serialize_proportional_rectangle_lookup(self.image_rectangles_by_filename),
                "samba": self.samba,
                "cots_waypoints": self.cots_waypoints,
                "has_data": self.has_data,
                "folder": self.folder
                }

        write_json_file(cache_file, dict)

# return true if successful
    def de_serialize(self):
        if self.samba:
            return False
        cache_file = self.cache_file()
        if not os.path.exists(cache_file):
            return False

        try:
            dict = read_json_file(cache_file)
            folder_from_cache = dict.get("folder")
            if folder_from_cache is None or folder_from_cache != self.folder:
                return False
            self.cots_detections_list = de_serialize_cots_detection_list(dict["cots_detections_list"])
            self.image_rectangles_by_filename = de_serialize_proportional_rectangle_lookup(dict["image_rectangles_by_filename"])
            self.samba = dict["samba"]
            self.cots_waypoints = dict["cots_waypoints"]
            self.has_data = dict["has_data"]
        except:
            return False
        return True


# returen the filename for the cache or serialization
    def cache_file(self):
        if self.eod:
            suffix = "eod"
        else:
            suffix = "rt"
        cache_folder = replace_last(self.folder, "/reefscan/", "/reefscan_cache/")
        if not os.path.isdir(cache_folder):
            os.makedirs(cache_folder)

        cache_file = f"{cache_folder}/cots_{suffix}.json"
        return cache_file

    # Function to get the related folder containing the eod json files
    def get_eod_detections_dir(self, images_folder):
        eod_json_dir = replace_last(images_folder, "/reefscan/", "/reefscan_eod_cots/")
        eod_json_dir = f"{eod_json_dir}/final"
        self.eod_detections_folder = eod_json_dir

    def get_scar_mask_file(self, photo_file):
        if self.eod_detections_folder is None:
            return None
        file_name = os.path.basename(photo_file).replace(".jpg", ".png")
        return self.eod_detections_folder + "/pixel_prediction_map_" + file_name


    # Read the real time cots detections from files
    # Returns true if the data is modified otherwise false
    def read_realtime_files(self, folder: str, samba: bool, use_cache=True):

        # If the folder is the same as the one passed
        if self.folder == folder:
            self.has_data = False
            return False

        self.folder = folder
        self.samba = samba
        self.eod = False
        self.eod_detections_folder = None
        # try cache first
        if use_cache:
            if self.de_serialize():
                return True

        self.cots_detections_list = []
        self.image_rectangles_by_filename = {}
        
        self.load_waypoints()
        self.read_realtime_sequence_files()
        self.read_realtime_image_files()
        self.has_data = True
        if not samba:
            self.serialize()
        return True

    def read_eod_files(self, folder: str, samba: bool, use_cache=True):
        if self.folder == folder:
            self.has_data = False
            return False

        self.folder = folder
        self.samba = samba
        self.eod = True
        self.get_eod_detections_dir(folder)
        # try cache first
        if use_cache:
            if self.de_serialize():
                return True

        self.cots_detections_list = []
        self.image_rectangles_by_filename = {}

        self.load_waypoints()
        self.read_eod_detection_files(folder, self.eod_detections_folder)
        self.has_data = True
        self.serialize()
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
            if ((filename.startswith("cots_image_") and filename.endswith(".json")) or filename.endswith(".jpg.json")) and ops.exists(file_path):
                try:
                    # Load the JSON content from local disk or samba drive
                    json_data = read_json_file_support_samba(file_path, self.samba)
                    results = json_data["results"]

                    sequence_ids = "sequences: "
                    comma = ", "
                    if len(results) > 0:
                        photo_file_name = ntpath.basename(json_data["header"]["frame_id"])
                        photo_file_name_path = f"{self.folder}/{photo_file_name}"
                        rectangles = []
                        max_score = 0
                        for result in results:
                            left = result["detection"]["left_x"]
                            top = result["detection"]["top_y"]
                            width = result["detection"]["width"]
                            height = result["detection"]["height"]
                            sequence_id = result["sequence_id"]
                            sequence_ids = f"{sequence_ids}{comma}{sequence_id}"
                            rectangle = ProportionalRectangle(left, top, width, height, sequence_id)
                            rectangles.append(rectangle)
                            for detection in result["detection"]["detection_results"]:
                                score = detection["score"]
                                if score > max_score:
                                    max_score = score

                        self.image_rectangles_by_filename[photo_file_name_path] = rectangles
                        waypoint_df = self.waypoint_by_filename(photo_file_name)
                        waypoint_df["sequence_ids"] = sequence_ids
                        waypoint_df["score"] = max_score
                        cots_waypoint_dfs.append(waypoint_df)
                except Exception as e:
                    logger.error(f"Error decoding JSON in {filename}: {e}", e)
        # concat the array of waypoint data frames into one and convert to a list
        if len(cots_waypoint_dfs) > 0:
            self.cots_waypoints = pd.concat(cots_waypoint_dfs).values.tolist()

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
                    confirmed = None
                    if 'confirmed' in json_data:
                        confirmed = json_data['confirmed']

                    cots_detections_info = CotsDetection(sequence_id=sequence_id,
                                                         best_class_id=best_class_id,
                                                         best_score=best_score,
                                                         confirmed=confirmed,
                                                         images=images
                                                         )
                    self.cots_detections_list.append(cots_detections_info)
                except Exception as e:
                    print(f"Error decoding JSON in {filename}: {e}")

    def read_eod_detection_files(self, folder: str, eod_cots_folder: str):
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

        # keep track of the sequence_id from the JSON which is not really sequence id but
        # is a count of the number of photos for this sequence so far
        # if if is a duplicate of the last one then it is a phantom detection
        sequence_counts = {}

        if os.path.exists(eod_cots_folder):
            print("building start")

            # Iterate through the json files in the eod cots folder
            files = ops.listdir(eod_cots_folder)
            files = sorted(files)
            for filename in files:
                file_path = f"{eod_cots_folder}/{filename}"

                # Check if the file is a JSON file
                if filename.endswith(".json") and os.path.isfile(file_path):
                    try:
                        # Load the JSON content from local disk or samba drive
                        json_data = read_json_file_support_samba(file_path, self.samba)

                        # Check if the file is an EOD COTS detection file based on keys
                        if 'frame_filename' and 'data' in json_data:
                            detections_list = json_data['data']['detections']
                            if len(detections_list) > 0:

                                photo_file_name = ntpath.basename(json_data["frame_filename"])
                                photo_file_name_path = f"{self.folder}/{photo_file_name}"

                                max_score=0
                                sequence_ids = "sequences: "
                                comma = ""
                                for detection in detections_list:
                                    class_id = 0
                                    sequence_id = detection['annotation_id']
                                    sequence_ids = f"{sequence_ids}{comma}{sequence_id}"
                                    comma = ", "
                                    score = detection['score']
                                    if score > max_score:
                                        max_score = score

                                    # Check if custom sequence json exists and read 'confirmed' field
                                    confirmed = None
                                    sequence_file = self.get_filename_cots_sequence(sequence_id)
                                    sequence_file_path = f"{eod_cots_folder}/{sequence_file}"
                                    if os.path.exists(sequence_file_path):
                                        sequence_json_data = read_json_file(sequence_file_path)
                                        if sequence_json_data['sequence_id'] == sequence_id:
                                            confirmed = sequence_json_data['confirmed']

                                    cots_detections_info = CotsDetection(sequence_id=sequence_id,
                                                                        best_class_id=class_id,
                                                                        best_score=score,
                                                                        confirmed=confirmed,
                                                                        images=[]
                                                                        )
                                    detection_ref.insert(cots_detections_info, photo_file_name_path)

                                cots_waypoint_df = self.waypoint_by_filename(photo_file_name)
                                cots_waypoint_df["sequence_ids"] = sequence_ids
                                cots_waypoint_df["score"] = max_score
                                cots_waypoint_dfs.append(cots_waypoint_df)
                                rectangles = []
                                for result in detections_list:
                                    px_left = result["x"]
                                    px_top = result["y"]
                                    px_width = result["width"]
                                    px_height = result["height"]
                                    sequence_id = result["annotation_id"]
                                    sequence_count = result['sequence_id']
                                    last_sequence_count = sequence_counts.get(sequence_id)
                                    phantom = (last_sequence_count is not None) and (last_sequence_count == sequence_count)
                                    sequence_counts[sequence_id] = sequence_count

                                    left, top, width, height = normalize_box_dims(photo_file_name_path, px_left, px_top, px_width, px_height)
                                    rectangle = ProportionalRectangle(left, top, width, height, sequence_id, phantom = phantom)
                                    rectangles.append(rectangle)
                                self.image_rectangles_by_filename[photo_file_name_path] = rectangles
                                # cots_waypoint_dfs.append(self.waypoint_by_filename(photo_file_name))

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {filename}: {e}")

            if len(cots_waypoint_dfs) > 0:
                self.cots_waypoints = pd.concat(cots_waypoint_dfs).values.tolist()

            else:
                self.cots_waypoints = []

        print ("building finished")
        # Convert the EOD detection dictionary to list
        self.cots_detections_list = detection_ref.extract_to_list()
        print ("list finished")

    def image_list(self, detection_list):
        images = []
        for detection in detection_list:
            try:
                photo_file_name = ntpath.basename(detection["filename"])
            except:
                # I changed the format while we are still in development but I want to support the old format for a little while
                photo_file_name = ntpath.basename(detection["image"]["header"]["frame_id"])
            images.append(f"{self.folder}/{photo_file_name}")
        return images

# read all waypoint for the reefscan sequence into a pandas data frane
    def load_waypoints (self):
        # if not self.samba:
        #     try:
        #         make_photo_csv(self.folder)
        #     except Exception as e:
        #         pass

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
        waypoint_df = self.waypoint_dataframe[self.waypoint_dataframe["filename_string"] == filename][["latitude", "longitude"]]
        return waypoint_df

    def get_index_by_sequence_id(self, sequence_id):
        idx = None
        for i in range(len(self.cots_detections_list)):
            if self.cots_detections_list[i].sequence_id == sequence_id:
                idx = i

        return idx


    def write_confirmed_field_to_cots_sequence(self, sequence_id):
        if self.eod:
            cots_folder = self.eod_detections_folder
        else:
            cots_folder = self.folder
        json_sequence_file = self.get_filename_cots_sequence(sequence_id)
        file_path = f"{cots_folder}/{json_sequence_file}"
        if os.path.exists(file_path):
            dict = read_json_file(file_path)
        else:
            dict = {}
            dict['sequence_id'] = sequence_id

        selected_idx = self.get_index_by_sequence_id(sequence_id)
        if selected_idx is not None:
            dict['confirmed'] = self.cots_detections_list[selected_idx].confirmed
            write_json_file(file_path, dict)
            self.serialize()


    def get_filename_cots_sequence(self, sequence_id):
        suffix = str(sequence_id).zfill(6)
        return f'cots_sequence_detection_{suffix}.json'