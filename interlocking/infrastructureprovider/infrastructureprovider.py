from abc import ABC, abstractmethod
import asyncio

class InfrastructureProvider(ABC):

    def __init__(self):
        self.tds_count_in_callback = None
        self.tds_count_out_callback = None

    #
    # Point Interaction
    #

    @abstractmethod
    async def turn_point(self, yaramo_point, target_orientation: str):
        """This method will be called when the interlocking controller wants to set the point. 
        The `yaramo_point` is the yaramo identifier of the point and `target_orientation` is one of `"left"` and  `"right"` """
        pass

    #
    # Signal Interaction
    #

    @abstractmethod
    async def set_signal_aspect(self, yaramo_signal, target_aspect):
        """This method will be called when the interlocking controller wants to change the signal-state of a specific signal. 
        `yaramo_signal` corresponds to the identifier of the signal in the yaramo model; `target_state` is one of `"halt"` and `"go"`.
        """
        pass

    #
    # Train Detection System
    #

    def _set_tds_count_in_callback(self, tds_count_in_callback):
        self.tds_count_in_callback = tds_count_in_callback

    async def tds_count_in(self, track_segment_id: str, train_id: str):
        """Adds a train to the segment identified by the `segment_id`"""
        await self.tds_count_in_callback(track_segment_id, train_id)

    def _set_tds_count_out_callback(self, tds_count_out_callback):
        self.tds_count_out_callback = tds_count_out_callback

    async def tds_count_out(self, track_segment_id, train_id: str):
        """Removes a train to the segment identified by the `segment_id`"""
        self.tds_count_out_callback(track_segment_id, train_id)
