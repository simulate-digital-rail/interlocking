from yaramo.model import SignalDirection
from .tracksegment import TrackSegment


class Track(object):

    def __init__(self, yaramo_edge):
        self.yaramo_edge = yaramo_edge
        self.base_track_id = yaramo_edge.uuid[-5:]
        self.signals = []
        self.left_point = None
        self.right_point = None
        self.segments = []

    def prepare_with_signals(self, signals):
        self.signals = signals
        self.signals.sort(key=lambda sig: sig.yaramo_signal.distance_edge, reverse=False)
        sum_of_lengths_so_far = 0
        for i in range(0, len(self.signals) + 1):
            if i < len(self.signals):
                length = self.signals[i].yaramo_signal.distance_edge - sum_of_lengths_so_far
                sum_of_lengths_so_far = sum_of_lengths_so_far + length
            else:
                length = self.yaramo_edge.length - sum_of_lengths_so_far
            segment = TrackSegment(f"{self.base_track_id}-{i}", self, length)
            self.segments.append(segment)

    def get_position_of_segment(self, segment):
        for i, _segment in enumerate(self.segments):
            if _segment.segment_id == segment.segment_id:
                return i
        return -1

    def is_first_segment(self, segment):
        return self.segments[0].segment_id == segment.segment_id

    def is_last_segment(self, segment):
        return self.segments[-1].segment_id == segment.segment_id

    def get_position_of_signal(self, signal):
        for i, _signal in enumerate(self.signals):
            if _signal.yaramo_signal.uuid == signal.yaramo_signal.uuid:
                return i
        return -1

    def get_segments_from_signal(self, signal):
        pos_in_track = self.get_position_of_signal(signal)
        if signal.yaramo_signal.direction == SignalDirection.IN:
            return self.segments[pos_in_track + 1:]
        else:
            return self.segments[:pos_in_track + 1]

    def get_segments_to_signal(self, signal):
        pos_in_track = self.get_position_of_signal(signal)
        if signal.yaramo_signal.direction == SignalDirection.IN:
            return self.segments[:pos_in_track + 1]
        else:
            return self.segments[pos_in_track + 1:]
