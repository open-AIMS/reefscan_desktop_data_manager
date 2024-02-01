class TowReefscanResults():
    def __init__(self):
        self.total_cots = 0
        self.probable_cots = 0
        self.confirmed_cots = 0
        self.total_scars = 0
        self.confirmed_scars = 0
        self.first_photo_time = None
        self.last_photo_time = None
        self.reefscan_hc_points =  0
        self.reefscan_total_points = 0

    def hc_cover(self):
        if self.reefscan_total_points == 0:
            return None
        else:
            return 100 * (self.reefscan_hc_points / self.reefscan_total_points)

