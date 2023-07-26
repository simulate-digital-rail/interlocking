from interlocking.interlockingcontroller import PointController, SignalController, TrackController, TrainDetectionController
from interlocking.infrastructureprovider import InfrastructureProvider
from interlocking.model import Point, Track, Signal, Route
from interlocking.model.helper import SetRouteResult, Settings, InterlockingOperationType
import asyncio
import time
import logging


class Interlocking(object):

    def __init__(self, infrastructure_providers, settings=Settings()):
        if not isinstance(infrastructure_providers, list):
            infrastructure_providers = [infrastructure_providers]
        self.infrastructure_providers = infrastructure_providers
        self.settings = settings

        self.point_controller = PointController(self.infrastructure_providers, self.settings)
        self.signal_controller = SignalController(self.infrastructure_providers)
        self.track_controller = TrackController(self, self.point_controller, self.signal_controller)
        self.train_detection_controller = TrainDetectionController(self.track_controller, self.infrastructure_providers)
        self.routes = []
        self.active_routes = []

    def prepare(self, yaramo_topoloy):
        # Nodes
        points = dict()
        for node_uuid in yaramo_topoloy.nodes:
            node = yaramo_topoloy.nodes[node_uuid]
            point = Point(node)
            points[point.point_id] = point
        self.point_controller.points = points

        # Signals
        signals = dict()
        for yaramo_signal_uuid in yaramo_topoloy.signals:
            yaramo_signal = yaramo_topoloy.signals[yaramo_signal_uuid]
            signal = Signal(yaramo_signal)
            signals[yaramo_signal.uuid] = signal
        self.signal_controller.signals = signals

        new_ip = InfrastructureProvider.verify_all_elements_covered_by_infrastructure_provider(yaramo_topoloy,
                                                                                               self.infrastructure_providers,
                                                                                               self.settings)
        if new_ip is not None:
            self.infrastructure_providers.append(new_ip)

        # Tracks
        tracks = dict()
        for edge_uuid in yaramo_topoloy.edges:
            edge = yaramo_topoloy.edges[edge_uuid]
            track = Track(edge)

            point_a = points[edge.node_a.uuid[-5:]]
            point_b = points[edge.node_b.uuid[-5:]]
            track.left_point = point_a
            track.right_point = point_b
            point_a.connect_track(track)
            point_b.connect_track(track)

            signals_of_track = []
            for signal_uuid in signals:
                signal = signals[signal_uuid]
                if signal.yaramo_signal.edge.uuid == edge.uuid:
                    signals_of_track.append(signal)
                    signal.track = track
            track.prepare_with_signals(signals_of_track)

            tracks[track.base_track_id] = track

        self.track_controller.tracks = tracks

        # Routes
        for yaramo_route_uuid in yaramo_topoloy.routes:
            yaramo_route = yaramo_topoloy.routes[yaramo_route_uuid]
            route = Route(yaramo_route)
            route.start_signal = signals[yaramo_route.start_signal.uuid]
            route.end_signal = signals[yaramo_route.end_signal.uuid]

            yaramo_edges_in_order = yaramo_route.get_edges_in_order()
            route_tracks = []
            for yaramo_edge in yaramo_edges_in_order:
                route_tracks.append(tracks[yaramo_edge.uuid[-5:]])
            route.tracks = route_tracks

            self.routes.append(route)

    async def run_with_operations_queue(self, operations_queue):
        next_op = await operations_queue.get()
        while next_op.operation_type != InterlockingOperationType.EXIT:
            op_type = next_op.operation_type
            if op_type == InterlockingOperationType.RESET:
                await self.reset()
            if op_type == InterlockingOperationType.PRINT_STATE:
                self.print_state()
            if op_type == InterlockingOperationType.SET_ROUTE:
                await self.set_route(next_op.yaramo_route, next_op.train_id)
            if op_type == InterlockingOperationType.FREE_ROUTE:
                self.free_route(next_op.yaramo_route, next_op.train_id)
            if op_type == InterlockingOperationType.RESET_ROUTE:
                await self.reset_route(next_op.yaramo_route, next_op.train_id)
            if op_type == InterlockingOperationType.TDS_COUNT_IN:
                await next_op.infrastructure_provider.tds_count_in(next_op.segment_id, next_op.train_id)
            if op_type == InterlockingOperationType.TDS_COUNT_OUT:
                await next_op.infrastructure_provider.tds_count_out(next_op.segment_id, next_op.train_id)
            operations_queue.task_done()
            next_op = await operations_queue.get()

    async def reset(self):
        self.point_controller.reset()
        self.track_controller.reset()
        await self.signal_controller.reset()
        self.active_routes = []

    def print_state(self):
        logging.debug("##############")
        self.point_controller.print_state()
        self.track_controller.print_state()
        self.signal_controller.print_state()

        logging.debug("Active Routes:")
        for active_route in self.active_routes:
            logging.debug(active_route.to_string())
        logging.debug("##############")

    async def set_route(self, yaramo_route, train_id: str):
        route_formation_time_start = time.time()
        set_route_result = SetRouteResult()
        if not self.can_route_be_set(yaramo_route, train_id):
            set_route_result.success = False
            return set_route_result
        route: Route = self.get_route_from_yaramo_route(yaramo_route)
        route.used_by = train_id
        self.active_routes.append(route)

        async with asyncio.TaskGroup() as tg:
            point_task = tg.create_task(self.point_controller.set_route(route, train_id))
            track_task = tg.create_task(self.track_controller.set_route(route, train_id))

        # Only set the signal to go if the points and tracks are processed
        if point_task.result() and track_task.result():
            set_route_result.success = await self.signal_controller.set_route(route)
            if not set_route_result.success:
                await self.reset_route(yaramo_route, train_id)
        else:
            # Set route failed, so the route has to be reset
            await self.reset_route(yaramo_route, train_id)
            set_route_result.success = False
        set_route_result.route_formation_time = time.time() - route_formation_time_start
        return set_route_result

    def can_route_be_set(self, yaramo_route, train_id: str):
        route = self.get_route_from_yaramo_route(yaramo_route)
        can_be_set = self.track_controller.can_route_be_set(route, train_id)
        can_be_set = can_be_set and self.point_controller.can_route_be_set(route, train_id)
        return can_be_set

    def do_two_routes_collide(self, yaramo_route_1, yaramo_route_2):
        route_1 = self.get_route_from_yaramo_route(yaramo_route_1)
        route_2 = self.get_route_from_yaramo_route(yaramo_route_2)
        do_collide = self.track_controller.do_two_routes_collide(route_1, route_2)
        do_collide = do_collide or self.point_controller.do_two_routes_collide(route_1, route_2)
        return do_collide

    def free_route(self, yaramo_route, train_id: str):
        route: Route = self.get_route_from_yaramo_route(yaramo_route)
        if route not in self.active_routes:
            raise Exception(f"Route from {yaramo_route.start_signal.name} to "
                            f"{yaramo_route.end_signal.name} was not set.")
        if route.used_by != train_id:
            raise Exception(f"Wrong Train ID: The route from {yaramo_route.start_signal.name} to "
                            f"{yaramo_route.end_signal.name} was not set with the train id "
                            f"{train_id}.")
        self.track_controller.free_route(route, train_id)
        self.active_routes.remove(route)
        route.used_by = None

    async def reset_route(self, yaramo_route, train_id: str):
        route: Route = self.get_route_from_yaramo_route(yaramo_route)
        if route not in self.active_routes:
            raise Exception(f"Route from {yaramo_route.start_signal.name} to "
                            f"{yaramo_route.end_signal.name} was not set.")
        if route.used_by != train_id:
            raise Exception(f"Wrong Train ID: The route from {yaramo_route.start_signal.name} to "
                            f"{yaramo_route.end_signal.name} was not set with the train id "
                            f"{train_id}.")
        self.point_controller.reset_route(route, train_id)
        self.track_controller.reset_route(route, train_id)
        self.train_detection_controller.reset_track_segments_of_route(route)
        await self.signal_controller.reset_route(route)
        self.active_routes.remove(route)
        route.used_by = None

    def get_route_from_yaramo_route(self, yaramo_route):
        for route in self.routes:
            if route.yaramo_route.uuid == yaramo_route.uuid:
                return route
        return None
