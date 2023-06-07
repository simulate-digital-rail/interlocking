from .overlapcontroller import OverlapController
from yaramo.model import SignalDirection
from interlocking.model import TrackSegmentState


class TrackController(object):

    def __init__(self, interlocking, point_controller, signal_controller):
        self.tracks = []
        self.interlocking = interlocking
        self.point_controller = point_controller
        self.signal_controller = signal_controller
        self.overlap_controller = OverlapController(interlocking, self, self.point_controller)

    def reset(self):
        for base_track_id in self.tracks:
            track = self.tracks[base_track_id]
            for segment in track.segments:
                segment.state = TrackSegmentState.FREE

    def set_route(self, route):
        self.reserve_route(route)

    def can_route_be_set(self, route):
        for segment in route.get_segments_of_route():
            if segment.state != TrackSegmentState.FREE:
                    print(f"{segment.segment_id} is not free")
                    return False
        return self.overlap_controller.can_any_overlap_be_reserved(route)

    def do_two_routes_collide(self, route_1, route_2):
        segments_of_route_1 = set(map(lambda seg: seg.segment_id, route_1.get_segments_of_route))
        segments_of_route_2 = set(map(lambda seg: seg.segment_id, route_2.get_segments_of_route))
        if len(segments_of_route_1.intersection(segments_of_route_2)) > 0:
            return True

        overlaps_of_route_1 = route_1.get_overlaps_of_route()
        found_no_free_overlap_route_1 = True
        for overlap in overlaps_of_route_1:
            overlap_segments = set(map(lambda seg: seg.segment_id, overlap.segments))
            if len(overlap_segments.intersection(segments_of_route_2)) == 0:
                found_no_free_overlap_route_1 = False
                break
        overlaps_of_route_2 = route_2.get_overlaps_of_route()
        found_no_free_overlap_route_2 = True
        for overlap in overlaps_of_route_2:
            overlap_segments = set(map(lambda seg: seg.segment_id, overlap.segments))
            if len(overlap_segments.intersection(segments_of_route_1)) == 0:
                found_no_free_overlap_route_2 = False
                break
        return found_no_free_overlap_route_1 or found_no_free_overlap_route_2

    def free_route(self, route):
        for segment in route.get_segments_of_route():
            print(f"--- Set track {segment.segment_id} free")
            segment.state = TrackSegmentState.FREE
        self.overlap_controller.free_overlap_of_route(route)

    def reset_route(self, route):
        self.free_route(route)

    def reserve_route(self, route):
        for segment in route.get_segments_of_route():
            print(f"--- Set track {segment.segment_id} reserved")
            segment.state = TrackSegmentState.RESERVED
        self.overlap_controller.reserve_overlap_of_route(route)

    def occupy_segment_of_track(self, segment):
        if segment.state != TrackSegmentState.OCCUPIED:
            print(f"--- Set track {segment.segment_id} occupied")
            segment.state = TrackSegmentState.OCCUPIED

            # Set signal to halt
            pos_of_segment = segment.track.get_position_of_segment(segment)
            if pos_of_segment > 0:
                previous_signal = segment.track.signals[pos_of_segment - 1]
                if previous_signal.yaramo_signal.direction == SignalDirection.IN:
                    self.signal_controller.set_signal_halt(previous_signal)
            if pos_of_segment < len(segment.track.signals):
                next_signal = segment.track.signals[pos_of_segment]
                if next_signal.yaramo_signal.direction == SignalDirection.GEGEN:
                    self.signal_controller.set_signal_halt(next_signal)

    def free_segment_of_track(self, segment):
        if segment.state != TrackSegmentState.FREE:
            print(f"--- Set track {segment.segment_id} free")
            segment.state = TrackSegmentState.FREE

            # Free point
            pos_of_segment = segment.track.get_position_of_segment(segment)
            if pos_of_segment == 0 or pos_of_segment == len(segment.track.signals) + 1:
                route = None
                for active_route in self.interlocking.active_routes:
                    if active_route.contains_segment(segment):
                        route = active_route
                        break
                if route is None:
                    raise ValueError("Active route not found")

                driving_direction = route.get_driving_direction_of_track_on_route(segment.track)

                if pos_of_segment == 0 and driving_direction == "in":
                    self.point_controller.set_point_free(segment.track.left_point)
                elif pos_of_segment == len(segment.track.signals) + 1 and driving_direction == "gegen":
                    self.point_controller.set_point_free(segment.track.right_point)

    def print_state(self):
        print("State of Tracks:")
        for base_track_id in self.tracks:
            track = self.tracks[base_track_id]
            for segment in track.segments:
                print(f"{segment.segment_id}: {segment.state}")
