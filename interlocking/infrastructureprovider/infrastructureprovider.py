from abc import ABC, abstractmethod
from yaramo.model import Node, Signal


class InfrastructureProvider(ABC):

    def __init__(self,
                 only_apply_for_signals: list[str] = None,
                 only_apply_for_points: list[str] = None,
                 apply_for_all_signals_except: list[str] = None,
                 apply_for_all_points_except: list[str] = None):
        if only_apply_for_signals is None:
            only_apply_for_signals = []
        self.only_apply_for_signals = only_apply_for_signals
        if only_apply_for_points is None:
            only_apply_for_points = []
        self.only_apply_for_points = only_apply_for_points
        if apply_for_all_signals_except is None:
            apply_for_all_signals_except = []
        self.apply_for_all_signals_except = apply_for_all_signals_except
        if apply_for_all_points_except is None:
            apply_for_all_points_except = []
        self.apply_for_all_points_except = apply_for_all_points_except

        if len(self.only_apply_for_signals) > 0 and len(self.apply_for_all_signals_except) > 0:
            raise Exception(f"You can not limit the infrastructure provider with only_apply_for_signals and "
                            f"apply_for_all_signals_except at the same time.")
        if len(self.only_apply_for_points) > 0 and len(self.apply_for_all_points_except) > 0:
            raise Exception(f"You can not limit the infrastructure provider with only_apply_for_points and "
                            f"apply_for_all_points_except at the same time.")

        self.tds_count_in_callback = None
        self.tds_count_out_callback = None

    #
    # Point Interaction
    #

    async def call_turn_point(self, yaramo_point: Node, target_orientation: str):
        point_id = yaramo_point.uuid[-5:]
        if point_id in self.only_apply_for_points:
            return await self.turn_point(yaramo_point, target_orientation)
        if len(self.only_apply_for_points) == 0 and point_id not in self.apply_for_all_points_except:
            return await self.turn_point(yaramo_point, target_orientation)

        # return True to skip this call and not prevent successfully turning of point.
        return True

    @abstractmethod
    async def turn_point(self, yaramo_point: Node, target_orientation: str):
        """This method will be called when the interlocking controller wants to set the point. 
        The `yaramo_point` is the yaramo identifier of the point and `target_orientation` is one of `"left"` and  `"right"` """
        pass

    #
    # Signal Interaction
    #

    async def call_set_signal_state(self, yaramo_signal: Signal, target_state: str):
        if yaramo_signal.name in self.only_apply_for_signals:
            return await self.set_signal_state(yaramo_signal, target_state)
        if len(self.only_apply_for_signals) == 0 and yaramo_signal.name not in self.apply_for_all_signals_except:
            return await self.set_signal_state(yaramo_signal, target_state)

        # return True to skip this call and not prevent successfully turning of point.
        return True

    @abstractmethod
    async def set_signal_state(self, yaramo_signal: Signal, target_state: str):
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
