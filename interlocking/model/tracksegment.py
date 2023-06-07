from .occupancystate import OccupancyState


class TrackSegment(object):

    def __init__(self, segment_id, track, length):
        self.segment_id = segment_id
        self.track = track
        self.state = OccupancyState.FREE
        self.used_by = []  # If segment is reserved, occupied or part of an overlap, this contains the train number(s).
        self.length = length
