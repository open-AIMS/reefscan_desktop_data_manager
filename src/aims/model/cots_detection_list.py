import csv
import json
import ntpath
import os
import pandas as pd

from PIL import Image
from PIL import UnidentifiedImageError
from pandas import DataFrame
from reefscanner.basic_model import exif_utils
from reefscanner.basic_model.json_utils import read_json_file
from reefscanner.basic_model.model_utils import replace_last
from reefscanner.basic_model.progress_queue import ProgressQueue
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops

from aims.model.cots_detection import CotsDetection, serialize_cots_detection_list, de_serialize_cots_detection_list
from aims.model.image_with_score import ImageWithScore
from aims.model.proportional_rectangle import ProportionalRectangle, serialize_proportional_rectangle_lookup, \
    de_serialize_proportional_rectangle_lookup

# This stores all the information for COTS detections for a reefscan sequence
from aims.operations.abstract_operation import AbstractOperation

from aims.utils import read_json_file_support_samba, read_json_file, write_json_file, short_file_name

import logging

from reefcloud.sub_sample import not_overlapping

logger = logging.getLogger("")


def photo_no(photo_file_name):
    num_str = photo_file_name[-8:-4]
    return int(num_str)


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
        
        self.load_waypoints(None)
        self.read_realtime_sequence_files()
        self.read_realtime_image_files()
        self.read_confirmations(None, self.folder)
        self.has_data = True
        self.sort_photos()
        if not samba:
            self.serialize()
        return True

    def read_eod_files(self, progress_queue: ProgressQueue, operation: AbstractOperation, folder: str, samba: bool, use_cache=True):
        progress_queue.reset()
        progress_queue.set_progress_label(f"Reading EOD detections for {folder}")

        if self.folder == folder:
            return False

        self.folder = folder
        self.samba = samba
        self.eod = True
        self.get_eod_detections_dir(folder)
        if not os.path.exists(self.eod_detections_folder):
            self.has_data = False
            return False
        # try cache first
        if use_cache:
            if self.de_serialize():
                return True

        self.cots_detections_list = []
        self.image_rectangles_by_filename = {}

        self.load_waypoints(progress_queue)
        self.read_eod_detection_files(progress_queue, operation, self.eod_detections_folder)
        self.sort_photos()

        if not operation.cancelled:
            self.read_confirmations(progress_queue, self.eod_detections_folder)
            self.has_data = True
            self.serialize()
        return True

    def sort_photos(self):
        for detection in self.cots_detections_list:
            detection:CotsDetection = detection
            detection.images.sort(key=lambda i: i.score, reverse=True)


# realtime confirmations are stores in a csv file. The csv file can have conflicting informations
# We always believe the most recent rows (ie towards the end of the file)
    def read_confirmations(self, progress_queue: ProgressQueue, folder):
        orig_csv_file_name= f"{folder}/cots_class_confirmations.csv"
        current_csv_file_name= f"{folder}/cots_class_confirmations_current.csv"
        if os.path.exists(current_csv_file_name):
            csv_file_name = current_csv_file_name
        else:
            csv_file_name = orig_csv_file_name


        if os.path.exists(csv_file_name):
            with open(csv_file_name, newline='') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for row in csv_reader:
                    sequence_id = int(row["detection_sequence"])
                    confirmed = None
                    if row["confirmed"] == "True":
                        confirmed = True
                    if row["confirmed"] == "False":
                        confirmed = False

                    index = self.get_index_by_sequence_id(sequence_id)
                    if index is not None:
                        detection: CotsDetection = self.cots_detections_list[index]
                        detection.confirmed = confirmed

    # Read the information from the cots_image_*.json files. Each file corresponds to a photo
    # and has the location of the COTS stored in the file as a rectangle (proprtional to the size of the photo)
    # This method populates image_rectangles_by_filename
    # json files may be on the local disks or a samba drive
    def read_realtime_image_files(self):
        ops = get_file_ops(self.samba)
        # this will be an array of single row data frames
        # one for each image with cots
        cots_waypoint_dfs = []
        confirmed = None
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
                        photo_file_name = filename[:len(filename)-5]
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

                            # cots_list_index = self.get_index_by_sequence_id(sequence_id)
                            # if cots_list_index:
                            #     cots_detection: CotsDetection = self.cots_detections_list[cots_list_index]
                            #     confirmed = cots_detection.confirmed

                        self.image_rectangles_by_filename[photo_file_name_path] = rectangles
                        waypoint_df = self.waypoint_by_filename(photo_file_name)
                        waypoint_df["sequence_ids"] = sequence_ids
                        waypoint_df["score"] = max_score
                        waypoint_df["photo_no"] = photo_no(photo_file_name)
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

                    cots_detections_info = CotsDetection(sequence_id=sequence_id,
                                                         best_class_id=best_class_id,
                                                         best_score=best_score,
                                                         confirmed=None,
                                                         images=images
                                                         )
                    self.cots_detections_list.append(cots_detections_info)
                except Exception as e:
                    print(f"Error decoding JSON in {filename}: {e}")

    def read_eod_detection_files(self, progress_queue: ProgressQueue, operation: AbstractOperation, eod_cots_folder: str):
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

            def insert(self, cots_detection_item: CotsDetection, image_path, score):
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
                    current_images.append(ImageWithScore(image_path, score))
                    self.reference_dict[sequence_id].images = current_images


            def extract_to_list(self):
                return [i for i in self.reference_dict.values()]

        detection_ref = EodDetectionsDict()
        self.cots_detections_list = []
        ops = get_file_ops(self.samba)

        # this will be an array of single row data frames
        # one for each image with cots
        cots_waypoint_dfs = []

        # scars don't have sequence ids so we make them up
        # negative so as to not clash with the COTS sequences
        cur_scar_sequence_id = 0
        this_sequence_start_exif = None
        current_scar_detection = None


        # keep track of the sequence_id from the JSON which is not really sequence id but
        # is a count of the number of photos for this sequence so far
        # if if is a duplicate of the last one then it is a phantom detection
        sequence_counts = {}

        if os.path.exists(eod_cots_folder):
            print("building start")

            # Iterate through the json files in the eod cots folder
            files = ops.listdir(eod_cots_folder)
            progress_queue.set_progress_max(len(files) + 1)
            files = sorted(files)
            for filename in files:
                if operation.cancelled:
                    return
                progress_queue.set_progress_value()

                file_path = f"{eod_cots_folder}/{filename}"

                # Check if the file is a JSON file
                if filename.endswith(".json") and os.path.isfile(file_path):
                    sequence_ids = None
                    try:
                        # Load the JSON content from local disk or samba drive
                        json_data = read_json_file_support_samba(file_path, self.samba)

                        # Check if the file is an EOD COTS detection file based on keys
                        if 'frame_filename' and 'data' in json_data:
                            photo_file_name = ntpath.basename(json_data["frame_filename"])
                            photo_file_name_path = f"{self.folder}/{photo_file_name}"
                            if 'pixel_prediction' in json_data['data']:
                                # scar_score = json_data['data']['pixel_prediction']['mean']
                                scar_score = json_data['data']['pixel_prediction']['max'] / 255
                                max_score=scar_score
                                # if scar_score > 0.01:
                                if scar_score > 0.5:
                                    this_photo_exif = exif_utils.get_exif_data(photo_file_name_path, True)
                                    if not_overlapping(this_sequence_start_exif, this_photo_exif):
                                        cur_scar_sequence_id -= 1
                                        this_sequence_start_exif = this_photo_exif
                                        current_scar_detection = CotsDetection(sequence_id=cur_scar_sequence_id,
                                                                             best_class_id=1,
                                                                             best_score=scar_score,
                                                                             confirmed=None,
                                                                             images=[]
                                                                             )

                                    sequence_ids = f"sequences: {cur_scar_sequence_id}"
                                    detection_ref.insert(current_scar_detection, photo_file_name_path, scar_score)

                            detections_list = json_data['data']['detections']
                            if len(detections_list) > 0:
                                confirmed = None
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
                                    detection_ref.insert(cots_detections_info, photo_file_name_path, score)

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
#                                cots_waypoint_dfs.append(self.waypoint_by_filename(photo_file_name))

                            if (sequence_ids is not None):
                                cots_waypoint_df = self.waypoint_by_filename(photo_file_name)
                                cots_waypoint_df["sequence_ids"] = sequence_ids
                                cots_waypoint_df["score"] = max_score
                                cots_waypoint_df["photo_no"] = photo_no(photo_file_name)
                                cots_waypoint_dfs.append(cots_waypoint_df)


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
            photo_file_name = ntpath.basename(detection["filename"])
            score = detection["detection_results"][0]["score"]

            images.append(ImageWithScore(f"{self.folder}/{photo_file_name}", score))
        return images

# read all waypoint for the reefscan sequence into a pandas data frane
    def load_waypoints (self, progress_queue: ProgressQueue):
        # if not self.samba
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
        waypoint_df:DataFrame = self.waypoint_dataframe[self.waypoint_dataframe["filename_string"] == short_file_name(filename)][["latitude", "longitude"]]
        if waypoint_df.size == 0:
            waypoint_df = self.waypoint_dataframe[self.waypoint_dataframe["filename_string"] == filename][["latitude", "longitude"]]
        return waypoint_df

    def get_index_by_sequence_id(self, sequence_id):
        idx = None
        for i in range(len(self.cots_detections_list)):
            if self.cots_detections_list[i].sequence_id == sequence_id:
                idx = i

        # if idx is None:
        #     raise Exception (f"index not found for sequence {sequence_id}")
        return idx

    def get_detection_by_sequence_id(self, sequence_id):
        idx = self.get_index_by_sequence_id(sequence_id)
        return self.cots_detections_list[idx] if idx else None

    def get_confirmed_by_sequence_id(self, sequence_id):
        idx = self.get_index_by_sequence_id(sequence_id)
        return self.cots_detections_list[idx].confirmed if idx else None

    def write_confirmed_field_to_cots_sequence(self):

        if self.eod:
            cots_folder = self.eod_detections_folder
        else:
            cots_folder = self.folder

        if cots_folder is None:
            raise Exception('Confirmations are not allowed when camera is "Both"')

        file_name = f"{cots_folder}/cots_class_confirmations_current.csv"
        with open(file_name, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["confirmed", "detection_sequence"], lineterminator="\n")
            writer.writeheader()
            for detection in self.cots_detections_list:
                msg_dict = {"confirmed": detection.confirmed, "detection_sequence": detection.sequence_id}
                writer.writerow(msg_dict)
        self.serialize()



    def get_filename_cots_sequence(self, sequence_id):
        suffix = str(sequence_id).zfill(6)
        return f'cots_sequence_detection_{suffix}.json'



# def cat_detection_lists(list1: CotsDetectionList, list2: CotsDetectionList):
#     big_list = CotsDetectionList()
#
#     big_list.cots_detections_list.extend(list1.cots_detections_list)
#     big_list.cots_detections_list.extend(list2.cots_detections_list)
#
#     big_list.image_rectangles_by_filename.update(list1.image_rectangles_by_filename)
#     big_list.image_rectangles_by_filename.update(list2.image_rectangles_by_filename)
#
#     big_list.cots_waypoints.extend(list1.cots_waypoints)
#     big_list.cots_waypoints.extend(list2.cots_waypoints)
#
#     big_list.has_data = list1.has_data or list2.has_data
#     return big_list

if __name__ == "__main__":
    print(photo_no("REEFSCAN_12_cam1_20241125_053944_689_0001.jpg"))
