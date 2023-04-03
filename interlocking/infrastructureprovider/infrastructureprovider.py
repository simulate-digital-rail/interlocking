from abc import ABC, abstractmethod


class InfrastructureProvider(ABC):

    def __init__(self):
        self.tds_count_in_callback = None
        self.tds_count_out_callback = None

    #
    # Point Interaction
    #

    @abstractmethod
    def turn_point(self, yaramo_point, target_orientation):
        pass

    #
    # Signal Interaction
    #

    @abstractmethod
    def set_signal_state(self, yaramo_signal, target_state):
        pass

    #
    # Train Detection System
    #

    def set_tds_count_in_callback(self, tds_count_in_callback):
        self.tds_count_in_callback = tds_count_in_callback

    def tds_count_in(self, track_segment_id):
        self.tds_count_in_callback(track_segment_id)

    def set_tds_count_out_callback(self, tds_count_out_callback):
        self.tds_count_out_callback = tds_count_out_callback

    def tds_count_out(self, track_segment_id):
        self.tds_count_out_callback(track_segment_id)
