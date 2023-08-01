import logging
from abc import ABC, abstractmethod
from yaramo.model import Node, Signal, Topology


class InfrastructureProvider(ABC):

    def __init__(self,
                 apply_for_signals: bool = True,
                 apply_for_points: bool = True,
                 only_apply_for_signals: list[str] = None,
                 only_apply_for_points: list[str] = None,
                 apply_for_all_signals_except: list[str] = None,
                 apply_for_all_points_except: list[str] = None):
        self.apply_for_signals = apply_for_signals
        self.apply_for_points = apply_for_points

        if not self.apply_for_points and not self.apply_for_signals:
            raise Exception("The infrastructure provider has to apply for signals, points or both.")

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

    def is_point_covered(self, yaramo_point: Node):
        if not self.apply_for_points:
            return False
        point_id = yaramo_point.uuid[-5:]
        return point_id in self.only_apply_for_points or \
            (len(self.only_apply_for_points) == 0 and point_id not in self.apply_for_all_points_except)

    async def call_turn_point(self, yaramo_point: Node, target_orientation: str):
        if self.is_point_covered(yaramo_point):
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

    def is_signal_covered(self, yaramo_signal: Signal):
        if not self.apply_for_signals:
            return False
        return yaramo_signal.name in self.only_apply_for_signals or \
            (len(self.only_apply_for_signals) == 0 and yaramo_signal.name not in self.apply_for_all_signals_except)

    async def call_set_signal_aspect(self, yaramo_signal: Signal, target_state: str):
        if self.is_signal_covered(yaramo_signal):
            return await self.set_signal_aspect(yaramo_signal, target_state)
        # return True to skip this call and not prevent successfully turning of signal.
        return True

    @abstractmethod
    async def set_signal_aspect(self, yaramo_signal: Signal, target_aspect: str):
        """This method will be called when the interlocking controller wants to change the signal-aspect of a specific signal.
        `yaramo_signal` corresponds to the identifier of the signal in the yaramo model; `target_aspect` is one of `"halt"` and `"go"`.
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

    #
    # Verify that all elements are covered by some infrastructure providers and add a default provider if not
    #

    @staticmethod
    def verify_all_elements_covered_by_infrastructure_provider(topology: Topology, infrastructure_providers, settings):
        uncovered_signals = []
        uncovered_points = []

        for signal in list(topology.signals.values()):
            if not any(ip.is_signal_covered(signal) for ip in infrastructure_providers):
                logging.warning(f"The signal {signal.name} is not covered by any infrastructure provider.")
                uncovered_signals.append(signal.name)

        for point in list(topology.nodes.values()):
            if len(point.connected_nodes) != 3:
                continue  # Skip all track ends
            if not any(ip.is_point_covered(point) for ip in infrastructure_providers):
                point_id = point.uuid[-5:]
                logging.warning(f"The point {point_id} is not covered by any infrastructure provider.")
                uncovered_points.append(point_id)

        if len(uncovered_signals) > 0 or len(uncovered_points) > 0:
            if settings.default_interlocking_provider is not None:
                return settings.default_interlocking_provider(apply_for_points=len(uncovered_points) > 0,
                                                              apply_for_signals=len(uncovered_signals) > 0,
                                                              only_apply_for_points=uncovered_points,
                                                              only_apply_for_signals=uncovered_signals)
        return None


