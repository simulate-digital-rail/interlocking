from planprohelper import PlanProHelper
from interlockingcontroller import PointController, SignalController, TrackController, TrainDetectionController
from model import Point, Track, Signal, Route


class Interlocking(object):

    def __init__(self, move_point_callback, set_signal_state_callback):
        self.point_controller = PointController(move_point_callback)
        self.signal_controller = SignalController(set_signal_state_callback)
        self.track_controller = TrackController(self, self.point_controller, self.signal_controller)
        self.train_detection_controller = TrainDetectionController(self.track_controller)
        self.stations = None
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

        # Tracks
        tracks = dict()
        for edge_uuid in yaramo_topoloy.edges:
            edge = yaramo_topoloy.edges[edge_uuid]
            track = Track(edge)

            point_a = points[edge.node_a.uuid[-5:]]
            point_b = points[edge.node_a.uuid[-5:]]
            track.left_point = point_a
            track.right_point = point_b
            point_a.connect_track(track)
            point_b.connect_track(track)

            signals_of_track = []
            for signal in signals:
                if signal.yaramo_signal.edge.uuid == edge.uuid:
                    signals_of_track.append(signal)
                    signal.track = track
            track.set_signals(signals_of_track)

            tracks[track.base_track_id] = track

        self.track_controller.tracks = tracks

        # Routes
        routes = dict()
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

            routes[yaramo_route_uuid] = route

    def reset(self):
        self.point_controller.reset()
        self.track_controller.reset()
        self.signal_controller.reset()
        self.active_routes = []

    def print_state(self):
        self.point_controller.print_state()
        self.track_controller.print_state()
        self.signal_controller.print_state()

        print("Active Routes:")
        for active_route in self.active_routes:
            print(active_route.to_string())

    def set_route(self, route, train):
        if not self.can_route_be_set(route):
            return False
        self.active_routes.append(route)
        self.point_controller.set_route(route)
        self.track_controller.set_route(route, train)
        self.signal_controller.set_route(route)
        return True

    def can_route_be_set(self, route):
        can_be_set = self.track_controller.can_route_be_set(route)
        can_be_set = can_be_set and self.point_controller.can_route_be_set(route)
        return can_be_set

    def do_two_routes_collide(self, route_1, route_2):
        do_collide = self.track_controller.do_two_routes_collide(route_1, route_2)
        do_collide = do_collide or self.point_controller.do_two_routes_collide(route_1, route_2)
        return do_collide

    def free_route(self, route):
        self.track_controller.free_route(route)
        self.active_routes.remove(route)
