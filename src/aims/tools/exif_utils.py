from datetime import datetime
from fractions import Fraction

import piexif

def get_date_time_orig(photo):
    try:
        exif_dict = piexif.load(photo)
        return exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
    except:
        raise Exception("Can't get exif data for " + photo)

def get_exif_data(photo, include_gps):
    exif_date_time_format = "%Y:%m:%d %H:%M:%S"
    try:
        exif_dict = piexif.load(photo)
    except:
        raise Exception("Can't get exif data for " + photo)

    try:
        if include_gps:
            gps = exif_dict["GPS"]
            (lat, lon) = get_coordinates(gps)
        else:
            lat = None
            lon = None
        datetime_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized].decode("utf-8")
        date_taken = datetime.strptime(datetime_str, exif_date_time_format)
        datetime_orig_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
        datetime_orig = datetime.strptime(datetime_orig_str, exif_date_time_format)
    except Exception as e:
        raise Exception("Can't get exif data for " + photo, e)

    return {"latitude": lat, "longitude": lon, "date_taken": date_taken, "date_time_orig": datetime_orig}


def get_coordinates(geotags):
    try:
        lat = get_decimal_from_dms(geotags[piexif.GPSIFD.GPSLatitude], geotags[piexif.GPSIFD.GPSLatitudeRef])
        lon = get_decimal_from_dms(geotags[piexif.GPSIFD.GPSLongitude], geotags[piexif.GPSIFD.GPSLongitudeRef])
    except:
        return None, None

    return lat, lon


def get_decimal_from_dms(dms, ref):
    degrees = dms[0][0] / dms[0][1]
    minutes = dms[1][0] / dms[1][1] / 60.0
    seconds = dms[2][0] / dms[2][1] / 3600.0

    if ref in [b'S', b'W', 'S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 5)


def convert_to_rational(number):
    if number < 0:
        print("{} is negative. How did that happen??".format(number))
        return 0, 0
    rational_fraction = Fraction(str(number))
    return (rational_fraction.numerator, rational_fraction.denominator)


def decimal_degrees_to_dms(decimal_number):
    degrees_value = int(abs(decimal_number))
    minutes_value = int((abs(decimal_number) - degrees_value) * 60)
    seconds_value = round((((abs(decimal_number) - degrees_value)) * 60 - minutes_value) * 60, 5)
    return (convert_to_rational(degrees_value),
            convert_to_rational(minutes_value),
            convert_to_rational(seconds_value))

def has_gps(exif_dict: dict):
    return "GPS" in exif_dict.keys()

def has_lat_lon(exif_dict: dict):
    piexif.ExifIFD
    if not has_gps(exif_dict):
        return False

    lat, lon = get_coordinates(exif_dict["GPS"])
    if lat is None:
        return False

    if lon is None:
        return False

    if lat < 0.0000001 and lat > -0.0000001:
        return False

    if lon < 0.0000001 and lon > -0.0000001:
        return False

    return True



def generate_gps_exif_dictionary(
        orig_gps_dict,
    latitude,
    longitude,
    gps_time_string):

    gpsifd_dict = orig_gps_dict

    messages = ""

    try:
        # Generate GPS Time String from time_stamp
        gpsifd_dict[piexif.GPSIFD.GPSDateStamp] = gps_time_string
    except:
        messages = messages + " Cannot get time"

    try:
    # Identify GPS Location Reference, i.e. "N" or "S", "E" or "W" based on sign of lat/lon
        if latitude < 0:
            gpsifd_dict[piexif.GPSIFD.GPSLatitudeRef] = "S"
        else:
            gpsifd_dict[piexif.GPSIFD.GPSLatitudeRef] = "N"
        if longitude < 0:
            gpsifd_dict[piexif.GPSIFD.GPSLongitudeRef] = "W"
        else:
            gpsifd_dict[piexif.GPSIFD.GPSLongitudeRef] = "E"

        gpsifd_dict[piexif.GPSIFD.GPSLatitude] = decimal_degrees_to_dms(latitude)
        gpsifd_dict[piexif.GPSIFD.GPSLongitude] = decimal_degrees_to_dms(longitude)

    except:
        messages = messages + " Cannot find GPS"

    return gpsifd_dict, messages
