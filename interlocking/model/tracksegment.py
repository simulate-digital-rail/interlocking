from .occupancystate import OccupancyState


class TrackSegment(object):

    def __init__(self, segment_id, track, length):
        self.segment_id = segment_id
        self.track = track
        self.state = OccupancyState.FREE
        self.length = length
        self.train = None  # If segment is reserved or occupied, this contains the train number
