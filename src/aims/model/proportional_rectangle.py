
# stores the location of a detected COTS within a photo
# the numbers a proportional to the size of the photo
class ProportionalRectangle:
    def __init__(self, left: str, top: str, width: str, height: str, sequence_id: str):
        self.left = float(left)
        self.top = float(top)
        self.width = float(width)
        self.height = float(height)
        self.sequence_id = sequence_id
