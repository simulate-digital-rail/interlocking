class Settings(object):

    def __init__(self, max_number_of_points_at_same_time=5):
        self.max_number_of_points_at_same_time = max(max_number_of_points_at_same_time, 1)
