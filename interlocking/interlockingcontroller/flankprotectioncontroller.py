from .signalcontroller import SignalController
from interlocking.model import Route, Point, OccupancyState, Signal
from yaramo.model import SignalDirection, NodeConnectionDirection
import logging


class FlankProtectionController(object):

    def __init__(self, point_controller, signal_controller: SignalController):
        self.point_controller = point_controller
        self.signal_controller = signal_controller

    def reset(self):
        for point in self.point_controller.points.values():
            point.is_used_for_flank_protection = False
        for signal in self.signal_controller.signals.values():
            signal.is_used_for_flank_protection = False

    async def add_flank_protection_for_point(self, point: Point, point_orientation: str,
                                             route: Route, train_id: str) -> bool:
        signals, points = self._get_flank_protection_elements_of_point(point, point_orientation)
        results = []
        for signal in signals:
            logging.info(f"--- Use signal {signal.yaramo_signal.name} for flank protection as 'halt-zeigendes Signal'")
            change_successful = await self.signal_controller.set_signal_halt(signal)
            results.append(change_successful)
            if change_successful:
                signal.is_used_for_flank_protection = True
        for point in points:
            orientation = points[point]
            if orientation is not None:
                # In case of a Schutztansportweiche the orientation is not relevant (None).
                logging.info(f"--- Use point {point.point_id} for flank protection as 'Schutzweiche'")
                change_successful = await self.point_controller.turn_point(point, orientation)
                results.append(change_successful)
                if change_successful:
                    point.is_used_for_flank_protection = True
            else:
                logging.info(f"--- Use point {point.point_id} for flank protection as 'Schutztransportweiche'")
                point.is_used_for_flank_protection = True
        return all(results)

    def free_flank_protection_of_point(self, point: Point, point_orientation: str):
        signals, points = self._get_flank_protection_elements_of_point(point, point_orientation)
        for signal in signals:
            signal.is_used_for_flank_protection = False
        for point in points:
            point.is_used_for_flank_protection = False

    def _get_flank_protection_elements_of_point(self,
                                                point: Point,
                                                point_orientation: str | None) -> tuple[list[Signal],
                                                                       dict[Point, str | None]]:
        flank_protection_tracks = []
        if point_orientation is None:
            # It's only none, iff there is a flank protection transport point (where the flank
            # protection area comes from Spitze
            flank_protection_tracks = [point.left, point.right]
        elif point_orientation == "left":
            flank_protection_tracks = [point.right]
        elif point_orientation == "right":
            flank_protection_tracks = [point.left]

        signal_results: list[Signal] = []
        point_results: dict[Point, str | None] = {}

        for flank_protection_track in flank_protection_tracks:
            # Search for signals
            yaramo_edge = flank_protection_track.yaramo_edge
            node_a = point.yaramo_node
            node_b = yaramo_edge.get_other_node(node_a)
            direction = yaramo_edge.get_direction_based_on_nodes(node_a, node_b)

            opposite_direction = SignalDirection.IN
            if direction == SignalDirection.IN:
                opposite_direction = SignalDirection.GEGEN
            yaramo_signals_in_direction = yaramo_edge.get_signals_with_direction_in_order(opposite_direction)
            # If there is any signal, take the closest one to the point and use it as halt-showing signal.
            found_signal = False
            if len(yaramo_signals_in_direction) > 0:
                yaramo_signal = yaramo_signals_in_direction[-1]  # Take the last one, which is the closest one.
                for signal_uuid in self.signal_controller.signals:
                    if signal_uuid == yaramo_signal.uuid:
                        signal_results.append(self.signal_controller.signals[signal_uuid])
                        found_signal = True
                        break

            # No Halt zeigendes Signal detected. Try to find Schutzweiche
            if not found_signal:
                other_point: Point | None = None
                for point_uuid in self.point_controller.points:
                    _point: Point = self.point_controller.points[point_uuid]
                    if node_b.uuid == _point.yaramo_node.uuid:
                        other_point = _point

                if other_point is not None and other_point.is_point:
                    connection_direction = other_point.get_connection_direction_of_track(flank_protection_track)
                    if connection_direction == NodeConnectionDirection.Spitze:
                        point_results[other_point] = None
                        signal_results, sub_point_results = self._get_flank_protection_elements_of_point(other_point, None)
                        point_results = point_results | sub_point_results
                    elif connection_direction == NodeConnectionDirection.Links:
                        point_results[other_point] = "right"
                    elif connection_direction == NodeConnectionDirection.Rechts:
                        point_results[other_point] = "left"
        return signal_results, point_results
