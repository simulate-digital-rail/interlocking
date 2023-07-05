from .signalcontroller import SignalController
from interlocking.model import Route, Point, OccupancyState, Signal
from yaramo.model import SignalDirection, NodeConnectionDirection


class FlankProtectionController(object):

    def __init__(self, point_controller, signal_controller: SignalController):
        self.point_controller = point_controller
        self.signal_controller = signal_controller

    def reset(self):
        # Do nothing, all will be done in the point and signal controller
        pass

    async def add_flank_protection_for_point(self, point: Point, point_orientation: str,
                                             route: Route, train_id: str) -> bool:
        signals, points = self._get_flank_protection_elements_of_point(point, point_orientation, route)
        results = []
        for signal in signals:
            print(f"Use {signal.yaramo_signal.name} as flank protection")
            signal.state = OccupancyState.FLANK_PROTECTION
            signal.used_by.add(train_id)
            results.append(await self.signal_controller.set_signal_halt(signal))
        for point in points:
            occupancy_state, orientation = points[point]
            point.state = occupancy_state
            point.used_by.add(train_id)
            if orientation is not None:
                # In case of a Schutztansportweiche the orientation is not relevant (None).
                results.append(await self.point_controller.turn_point(point, orientation))
        return all(results)

    def free_flank_protection_of_point(self, point: Point, point_orientation: str, route: Route, train_id: str):
        signals, points = self._get_flank_protection_elements_of_point(point, point_orientation, route)
        for signal in signals:
            self.signal_controller.free_signal(signal, train_id)
        for point in points:
            self.point_controller.set_point_free(point, train_id)

    def _get_flank_protection_elements_of_point(self,
                                                point: Point,
                                                point_orientation: str,
                                                route: Route) -> tuple[list[Signal],
                                                                       dict[Point, tuple[OccupancyState, str | None]]]:
        flank_protection_track = point.left
        if point_orientation == "left":
            flank_protection_track = point.right

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
        if len(yaramo_signals_in_direction) > 0:
            yaramo_signal = yaramo_signals_in_direction[0]
            for signal_uuid in self.signal_controller.signals:
                if signal_uuid == yaramo_signal.uuid:
                    return [self.signal_controller.signals[signal_uuid]], {}
            raise ValueError("yaramo signal has no corresponding interlocking signal")

        # No Halt zeigendes Signal detected. Try to find Schutzweiche
        other_point: Point | None = None
        for point_uuid in self.point_controller.points:
            point: Point = self.point_controller.points[point_uuid]
            if node_b.uuid == point.yaramo_node.uuid:
                other_point = point

        if other_point is not None and other_point.is_point:
            connection_direction = other_point.get_connection_direction_of_track(flank_protection_track)
            if connection_direction == NodeConnectionDirection.Spitze:
                point_results = {other_point: (OccupancyState.FLANK_PROTECTION_TRANSPORT, None)}
                # Recursive
                return [], point_results
            if connection_direction == NodeConnectionDirection.Links:
                return [], {other_point: (OccupancyState.FLANK_PROTECTION, "right")}
            if connection_direction == NodeConnectionDirection.Rechts:
                return [], {other_point: (OccupancyState.FLANK_PROTECTION, "left")}
        return [], {}
