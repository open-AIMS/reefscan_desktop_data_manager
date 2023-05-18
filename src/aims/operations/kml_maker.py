import os

import simplekml
from reefscanner.basic_model.photo_csv_maker import track
from reefscanner.basic_model.survey import Survey


def make_kml(survey: Survey):
    folder = survey.folder
    points = track(folder, False)
    if os.path.isdir(folder):
        kml_file_name = f"{folder}.kml"
        kml = simplekml.Kml()
        for point in points:
            kml.newpoint(coords=[(point[1], point[0])])

        kml.save(kml_file_name)


