from PyQt5.QtCore import QObject

# Stores all the information for one cots detection sequence
# A sequence represents one individual COTS
# This individual will be tracked through one or more images
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