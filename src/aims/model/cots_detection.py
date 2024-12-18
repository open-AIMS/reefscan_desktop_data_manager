from PyQt5.QtCore import QObject

# Stores all the information for one cots detection sequence
# A sequence represents one individual COTS
# This individual will be tracked through one or more images

# serialize and de-serialize to dicts
from aims.model.image_with_score import deserialize_image_with_score


def de_serialize_cots_detection(dict):
    images=[]
    for image_dict in dict["images"]:
        images.append(deserialize_image_with_score(image_dict))

    return CotsDetection(sequence_id = dict["sequence_id"],
                         best_class_id = dict["best_class_id"],
                         best_score = dict["best_score"],
                         images = images,
                         avg_score= dict["avg_score"],
                         confirmed= dict["confirmed"],
                         )
def de_serialize_cots_detection_list(list):
    return_list = []
    for dict in list:
        return_list.append(de_serialize_cots_detection(dict))
    return return_list

def serialize_cots_detection_list(list):
    return_list = []
    for cots_detection in list:
        return_list.append(cots_detection.serialize())
    return return_list

class CotsDetection:
    def __init__(self, sequence_id=None, best_class_id=None, best_score=None, confirmed=None, images=[], avg_score=None):
        self.sequence_id = sequence_id
        self.best_score = best_score
        self.avg_score = avg_score
        self.best_class_id = best_class_id
        if best_class_id == 0:
            self.best_class = "COTS"
        elif best_class_id == 1:
            self.best_class = "Scar"
        else:
            self.best_class = best_class_id

        self.confirmed = confirmed
        self.images = images

    def serialize(self):
        images_serialized = []
        for image in self.images:
            images_serialized.append(image.serialize())
        return {
            "sequence_id": self.sequence_id,
            "best_score": self.best_score,
            "best_class_id": self.best_class_id,
            "images": images_serialized,
            "avg_score": self.avg_score,
            "confirmed": self.confirmed,

        }