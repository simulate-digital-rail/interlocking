from .occupancystate import OccupancyState


class TrackSegment(object):

    def __init__(self, segment_id, track, length):
        self.segment_id = segment_id
        self.track = track
        self.state = OccupancyState.FREE
        self.used_by = set()  # If segment is reserved, occupied or part of an overlap, this contains the train numbers.
        self.length = length

    def is_only_used_by_train(self, train_id):
        return len(self.used_by) == 1 and train_id in self.used_by
