import fnmatch
import os
from datetime import datetime, timedelta

import gpxpy
import piexif
from reefscanner.basic_model.progress_queue import ProgressQueue

from aims.tools.exif_utils import generate_gps_exif_dictionary, get_coordinates, has_lat_lon, has_gps


class Geocode:
    def __init__(self, progress_queue: ProgressQueue):
        super().__init__()
        self.progress_queue = progress_queue
        self.canceled = False

    def make_geo_lookup(self, track_file):

        gpx_source_file = open(track_file, 'r')
        gpx_in = gpxpy.parse(gpx_source_file)

        lookup = {}
        for track in gpx_in.tracks:
            for segment in track.segments:
                for point in segment.points:
                    lookup[point.time] = {"lat": point.latitude, "lon": point.longitude}

        return lookup

    def geocode(self, gpx_file, image_folder, camera_diff_seconds, timezone):
        self.progress_queue.reset()
        self.progress_queue.set_progress_label(f"GeoTagging photos for {image_folder}")

        files = os.listdir(image_folder)
        photos = fnmatch.filter(files, "*.[Jj][Pp][Gg]")
        self.progress_queue.set_progress_max(len(photos))
        self.progress_queue.set_progress_value()

        exif_date_time_format = "%Y:%m:%d %H:%M:%S"
        exif_date_time_format_with_tz = exif_date_time_format + "%z"
        camera_diff = timedelta(seconds=camera_diff_seconds)

        if self.canceled:
            return False

        lookup = self.make_geo_lookup(gpx_file)


        i = 0
        changed=False
        should_change=False
        first = True
        for photo in photos:
            if self.canceled:
                return False
            photo_path = f"{image_folder}/{photo}"
            parent_dict = piexif.load(photo_path)
            exif_dict = parent_dict["Exif"]
            datetime_orig_str = exif_dict[piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
            datetime_orig = datetime.strptime(datetime_orig_str + timezone, exif_date_time_format_with_tz)
            datetime_new = datetime_orig + camera_diff
            datetime_new_str = datetime_new.strftime(exif_date_time_format).encode("utf-8")
            exif_dict[piexif.ExifIFD.DateTimeDigitized] = datetime_new_str
            if first:
                first_original_photo_date = datetime_orig_str
                first_corrected_photo_date = datetime_new_str

            if not has_lat_lon(parent_dict):
                should_change = True
                if datetime_new in lookup:
                    waypoint = lookup[datetime_new]
                    if has_gps(parent_dict):
                        orig_gps_dict = parent_dict["GPS"]
                    else:
                        orig_gps_dict = {}
                    gps_dict, messages = generate_gps_exif_dictionary (orig_gps_dict, waypoint["lat"], waypoint["lon"], datetime_new_str)
                    parent_dict["GPS"] = gps_dict

                    exif_bytes = piexif.dump(parent_dict)
                    piexif.insert(exif_bytes, photo_path)
                    changed = True

            self.progress_queue.set_progress_value()
            first = False

        last_original_photo_date = datetime_orig_str
        last_corrected_photo_date = datetime_new_str

        if changed:
            # rename the photo_log so when we try to see a map a new one will be created based on the exif values
            try:
                os.rename(f"{image_folder}/photo_log.csv", f"{image_folder}/photo_log.csv.no_gps")
            except:
                print("error renaming photo_log. Probably it has already been done")
        else:
            if should_change:
                lookup_keys = list(lookup.keys())
                first_gps_date = lookup_keys[0]
                last_gps_date = lookup_keys[len(lookup_keys) - 1]
                raise Exception(f"No photos changed.\n GPS dates are between {first_gps_date} and {last_gps_date}.\n Original Photo dates are between {first_original_photo_date} and {last_original_photo_date}\n Corrected Photo dates are between {first_corrected_photo_date} and {last_corrected_photo_date}")

if __name__ == "__main__":

    print ("hi")


