from enum import Enum


class TrackSegmentState(Enum):
    FREE = 0
    RESERVED = 1
    RESERVED_OVERLAP = 2
    OCCUPIED = 3


class TrackSegment(object):

    def __init__(self, segment_id, track, length):
        self.segment_id = segment_id
        self.track = track
        self.state = TrackSegmentState.FREE
        self.length = length
        self.train = None  # If segment is reserved or occupied, this contains the train number
