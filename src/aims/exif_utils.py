import piexif


def get_exif_data(photo):
    exif_dict = piexif.load(photo)
    print(exif_dict)
    gps = exif_dict["GPS"]
    return get_coordinates(gps)


def get_coordinates(geotags):
    lat = get_decimal_from_dms(geotags[piexif.GPSIFD.GPSLatitude], geotags[piexif.GPSIFD.GPSLatitudeRef])
    lon = get_decimal_from_dms(geotags[piexif.GPSIFD.GPSLongitude], geotags[piexif.GPSIFD.GPSLongitudeRef])
    date = geotags[piexif.GPSIFD.GPSDateStamp]
    date = "".join(map(chr, date))
    print(date)
    return (lat, lon, date)


def get_decimal_from_dms(dms, ref):
    degrees = dms[0][0] / dms[0][1]
    minutes = dms[1][0] / dms[1][1] / 60.0
    seconds = dms[2][0] / dms[2][1] / 3600.0

    if ref in [b'S', b'W', 'S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 5)
