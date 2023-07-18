from .occupancystate import OccupancyState
from yaramo.model import Signal as YaramoSignal


class Signal(object):

    def __init__(self, yaramo_signal: YaramoSignal):
        from interlocking.model import Track

        self.yaramo_signal = yaramo_signal
        self.signal_aspect: str = "undefined"  # Either halt or go
        self.state: OccupancyState = OccupancyState.FREE
        self.used_by = set()  # If point is reserved, occupied or part of an overlap, this contains the train numbers.
        self.track: Track or None = None
