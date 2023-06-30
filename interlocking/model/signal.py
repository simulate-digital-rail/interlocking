from .occupancystate import OccupancyState


class Signal(object):

    def __init__(self, yaramo_signal):
        self.yaramo_signal = yaramo_signal
        self.signal_aspect: str = "halt"  # Either halt or go
        self.state: OccupancyState = OccupancyState.FREE
        self.used_by = set()  # If point is reserved, occupied or part of an overlap, this contains the train numbers.
        self.track = None
