import json
import os
import shutil
import time

from PyQt5.QtCore import QObject
from reefscanner.basic_model.exif_utils import get_exif_data

import geopy.distance
from reefscanner.basic_model.progress_queue import ProgressQueue
import pandas as pd

from aims.state import state
import logging
logger = logging.getLogger("")

def wp(exif):
    return exif["latitude"], exif["longitude"]

def not_overlapping(exif1, exif2):
    if exif1 is None:
        return True

    return should_keep(wp(exif2), wp(exif1), exif1["subject_distance"], exif2["subject_distance"])


def should_keep(wp, old_wp, target_distance, subject_distance, maximum_target_distance=12):
    if subject_distance > maximum_target_distance:
        return False

    if target_distance is None:
        return True

    if old_wp is None:
        return True

    if wp is None:
        return False

    d = geopy.distance.distance(old_wp, wp).meters

    return d > target_distance


class SubSampler(QObject):
    def __init__(self):
        super().__init__()
        self.canceled = False

    def has_waypoints(self, folder):
        csv_file_name = folder + "/photo_log.csv"
        if os.path.exists(csv_file_name):
            with open(csv_file_name, mode="r") as file:
                df = pd.read_csv(file)
        else:
            return False
        total_photos = len(df)
        bad_photos = (df['latitude'].isna() | df['longitude'].isna()).sum()

        proportion_bad = bad_photos / total_photos
        return proportion_bad < 0.1

    def sub_sample_dir(self, image_dir, sample_dir, progress_queue: ProgressQueue):
        logger.info(f"sub_sample dir {time.process_time()}")
        progress_queue.reset()
        progress_queue.set_progress_label(f"initializing {image_dir}")

        os.makedirs(sample_dir, exist_ok=True)
        progress_queue.set_progress_value()

        if self.has_waypoints(image_dir):
            return self.sub_sample_dir_spatial(image_dir, sample_dir, progress_queue)
        else:
            return self.sub_sample_dir_simple(image_dir, sample_dir, progress_queue)

    def sub_sample_dir_spatial(self, image_dir, sample_dir, progress_queue: ProgressQueue):
        logger.info(f"sub_sample spatial {time.process_time()}")

        progress_queue.reset()
        _subsampling_folder = self.tr('Subsampling folder')
        progress_queue.set_progress_label(f"{_subsampling_folder} {image_dir}")


        listdir = os.listdir(image_dir)
        listdir.sort()
        old_wp = None
        selected_photo_infos = []
        target_distance = None

        maximum_subject_distance = int(state.reef_cloud_max_depth)
        progress_queue.set_progress_max(len(listdir)-1)
        for file_name in listdir:
            if self.canceled:
                return None

            if file_name.lower().endswith(".jpg"):
                full_file_name = image_dir + "/" + file_name
                try:
                    exif = get_exif_data(full_file_name, False)
                    subject_distance = exif["subject_distance"]
                    if subject_distance is None:
                        subject_distance = 8

                    if exif["latitude"] is None or exif["longitude"] is None:
                        keep = False

                    wp = exif["latitude"], exif["longitude"]
                    keep = should_keep(wp, old_wp, target_distance, subject_distance, maximum_subject_distance)

                    # Ignore photos with bad geolocation in exif data.
                except Exception as e:
                    print (e)
                    keep = False
                if keep:

                    shutil.copy2(full_file_name, sample_dir + "/" + file_name)
                    old_wp = wp
                    exif = get_exif_data(full_file_name, True)
                    exif["filename"] = file_name
                    selected_photo_infos.append(exif)
                    target_distance = subject_distance
            progress_queue.set_progress_value()
        return selected_photo_infos


    def sub_sample_dir_simple(self, image_dir, sample_dir, progress_queue: ProgressQueue):
        progress_queue.reset()

        _subsampling_folder = self.tr('Subsampling folder')
        progress_queue.set_progress_label(f"{_subsampling_folder} {image_dir}")


        listdir = os.listdir(image_dir)
        listdir.sort()
        progress_queue.set_progress_max(len(listdir)-1)

        i = 1
        selected_photo_infos = []

        for file_name in listdir:
            if file_name.lower().endswith(".jpg"):
                full_file_name = image_dir + "/" + file_name
                if i % 10 == 0:
                    exif = get_exif_data(full_file_name, True)
                    shutil.copy2(full_file_name, sample_dir + "/" + file_name)
                    exif["filename"] = file_name
                    selected_photo_infos.append(exif)

                i+=1
            progress_queue.set_progress_value()
        return selected_photo_infos

# def count_dir(good_dir):
#     sample_dir = good_dir.replace("/all/", "/sample/")
#     os.makedirs(sample_dir, exist_ok=True)
#
#     listdir = os.listdir(good_dir)
#     listdir.sort()
#     old_wp = None
#     good = 0
#     bad = 0
#     for f in listdir:
#         if f.lower().endswith(".jpg"):
#             fname = good_dir + "/" + f
#             try:
#                 wp = get_exif_data(fname)
#                 if wp is None:
#                     bad += 1
#                 else:
#                     good += 1
#             except:
#                 bad += 1
#     return f"good: {good}  bad: {bad}"
#
# root_dir = "D:/heron-for-reefcloud/extra/all/"
# dirs = os.listdir(root_dir)
# for this_dir in dirs:
#     full_path = root_dir + this_dir
#     if os.path.isdir(full_path):
#         logger.info(full_path)
#         sub_sample_dir_simple(full_path)
#         # sub_sample_dir(full_path)
#         # logger.info(count_dir(full_path))
#
#
#
