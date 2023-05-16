class Overlap(object):

    def __init__(self, required_length, route):
        self.points = []
        self.segments = dict()
        self.required_length = required_length
        self.missing_length = required_length
        self.route = route

    def is_full(self):
        return self.missing_length <= 0

    def add_segment(self, track, segment_id):
        if track not in self.segments:
            self.segments[track] = []
        self.segments[track].append(segment_id)
        self.missing_length = self.missing_length - track.lengths[segment_id]

    def duplicate(self):
        new_obj = Overlap(self.required_length, self.route)
        new_obj.missing_length = self.missing_length

        for point in self.points:
            new_obj.points.append(point)

        for track in self.segments:
            new_obj.segments[track] = []
            for segment_id in self.segments[track]:
                new_obj.segments[track].append(segment_id)
        return new_obj
