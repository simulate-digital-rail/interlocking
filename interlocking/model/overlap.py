class Overlap(object):

    def __init__(self, required_length, route):
        self.points = []
        self.segments = []
        self.required_length = required_length
        self.missing_length = required_length
        self.route = route

    def is_full(self):
        return self.missing_length <= 0

    def add_segment(self, segment):
        self.segments.append(segment)
        self.missing_length = self.missing_length - segment.length

    def duplicate(self):
        new_obj = Overlap(self.required_length, self.route)
        for point in self.points:
            new_obj.points.append(point)
        for segment in self.segments:
            new_obj.add_segment(segment)
        return new_obj
