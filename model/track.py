from yaramo.model import SignalDirection

class Track(object):

    def __init__(self, yaramo_edge):
        self.yaramo_edge = yaramo_edge
        self.base_track_id = yaramo_edge.uuid[-5:]
        self.state = dict()  # Either free, reserved or occupied
        self.signals = []
        self.lengths = dict()  # Segment id to segment length
        self.left_point = None
        self.right_point = None

    def set_signals(self, signals):
        self.signals = signals
        self.signals.sort(key=lambda sig: sig.yaramo_signal.distance_edge, reverse=False)
        sum_of_lengths_so_far = 0
        for i in range(0, len(self.signals) + 1):
            self.state[f"{self.base_track_id}-{i}"] = "free"
            if i < len(self.signals):
                self.lengths[f"{self.base_track_id}-{i}"] = self.signals[i].yaramo_signal.distance_edge \
                                                            - sum_of_lengths_so_far
                sum_of_lengths_so_far = sum_of_lengths_so_far + self.lengths[f"{self.base_track_id}-{i}"]

        self.lengths[f"{self.base_track_id}-{len(self.signals)}"] = len(self.yaramo_edge) - sum_of_lengths_so_far

    def get_position_of_segment(self, segment_id):
        if segment_id.endswith("-re"):
            segment_id = segment_id[:-3]
        return int(segment_id[segment_id.rfind("-") + 1:])

    def get_position_of_signal(self, signal):
        for i in range(0, len(self.signals)):
            if signal.yaramo_signal.uuid == self.signals[i].yaramo_signal.uuid:
                return i
        return -1

    def get_segments_of_range(self, from_index, to_index):
        result = []
        for i in range(from_index, to_index):
            result.append(f"{self.base_track_id}-{i}")
        return result

    def get_all_segments_of_track(self, track):
        return track.get_segments_of_range(0, len(track.signals)+1)

    def get_segments_from_signal(self, signal):
        pos_in_track = self.get_position_of_signal(signal)
        if signal.yaramo_signal.direction == SignalDirection.IN:
            return signal.track.get_segments_of_range(pos_in_track + 1, len(signal.track.signals) + 1)
        else:
            return signal.track.get_segments_of_range(0, pos_in_track + 1)

    def get_segments_to_signal(self, signal):
        pos_in_track = self.get_position_of_signal(signal)
        if signal.wirkrichtung == SignalDirection.IN:
            return signal.track.get_segments_of_range(0, pos_in_track + 1)
        else:
            return signal.track.get_segments_of_range(pos_in_track + 1, len(signal.track.signals) + 1)
