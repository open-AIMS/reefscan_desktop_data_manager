import json
import os
import shutil

from reefscanner.basic_model.exif_utils import get_exif_data

import geopy.distance


def should_keep(wp, old_wp, target_distance):
    if old_wp is None:
        return True

    if wp is None:
        return False

    d = geopy.distance.distance(old_wp, wp).meters

    return d > target_distance



def sub_sample_dir(image_dir, sample_dir):
    if os.path.exists (sample_dir):
        shutil.rmtree(sample_dir)
    os.makedirs(sample_dir, exist_ok=True)

    listdir = os.listdir(image_dir)
    listdir.sort()
    old_wp = None
    selected_photo_infos = []
    target_distance = None
    for f in listdir:
        if f.lower().endswith(".jpg"):
            fname = image_dir + "/" + f
            try:
                exif = get_exif_data(fname, False)
                if target_distance is None:
                    target_distance = exif["subject_distance"]

                wp = exif["latitude"], exif["longitude"]
                keep = should_keep(wp, old_wp, target_distance)
                # Ignore photos with bad geolocation in exif data.
                if exif["latitude"] is None or exif["longitude"] is None or "altitude" not in exif:
                    keep = False
            except Exception as e:
                print (e)
                keep = False
            if keep:
                shutil.copy2(fname, sample_dir)
                old_wp = wp
                exif = get_exif_data(fname, True)
                exif["filename"] = f
                selected_photo_infos.append(exif)

    return selected_photo_infos



def sub_sample_dir_simple(image_dir):
    good_dir = f"{image_dir}/good"
    sample_dir = f"{image_dir}/sample"

    os.makedirs(sample_dir, exist_ok=True)

    listdir = os.listdir(good_dir)
    listdir.sort()
    i = 1
    for f in listdir:
        if f.lower().endswith(".jpg"):
            fname = good_dir + "/" + f
            if i % 15 == 0:
                shutil.copy2(fname, sample_dir)
            i+=1

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
#         print(full_path)
#         sub_sample_dir_simple(full_path)
#         # sub_sample_dir(full_path)
#         # print(count_dir(full_path))
#
#
#
