from PyQt5.QtCore import QObject

# Stores all the information for one cots detection sequence
# A sequence represents one individual COTS
# This individual will be tracked through one or more images

# serialize and de-serialize to dicts
def de_serialize_cots_detection(dict):
    return CotsDetection(dict["sequence_id"],
                         dict["best_class"],
                         dict["best_score"],
                         dict["images"]
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
    def __init__(self, sequence_id=None, best_class_id=None, best_score=None, images=[]):
        self.sequence_id = sequence_id
        self.best_score = best_score
        if best_class_id == 0:
            self.best_class = "COTS"
        elif best_class_id == 1:
            self.best_class = "Scar"
        else:
            self.best_class = best_class_id

        self.images = images

    def serialize(self):
        return {
            "sequence_id": self.sequence_id,
            "best_score": self.best_score,
            "best_class": self.best_class,
            "images": self.images

        }