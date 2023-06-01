from .overlapcontroller import OverlapController
from yaramo.model import SignalDirection

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
            for segment_id in track.state:
                track.state[segment_id] = "free"

    async def set_route(self, route):
        return await self.reserve_route(route)

    def can_route_be_set(self, route):
        segments = route.get_segments_of_route()
        for track_base_id in segments:
            track = self.tracks[track_base_id]
            for segment_id in segments[track_base_id]:
                if track.state[segment_id] != "free":
                    return False
        return self.overlap_controller.can_any_overlap_be_reserved(route)

    def do_two_routes_collide(self, route_1, route_2):
        segments_of_route_1 = {x for v in route_1.get_segments_of_route().values() for x in v}
        segments_of_route_2 = {x for v in route_2.get_segments_of_route().values() for x in v}
        if len(segments_of_route_1.intersection(segments_of_route_2)) > 0:
            return True

        overlaps_of_route_1 = route_1.get_overlaps_of_route()
        found_no_free_overlap_route_1 = True
        for overlap in overlaps_of_route_1:
            overlap_segments_of_route_1 = {x for v in overlap.segments.values() for x in v}
            if len(overlap_segments_of_route_1.intersection(segments_of_route_2)) == 0:
                found_no_free_overlap_route_1 = False
                break
        overlaps_of_route_2 = route_2.get_overlaps_of_route()
        found_no_free_overlap_route_2 = True
        for overlap in overlaps_of_route_2:
            overlap_segments_of_route_2 = {x for v in overlap.segments.values() for x in v}
            if len(overlap_segments_of_route_2.intersection(segments_of_route_1)) == 0:
                found_no_free_overlap_route_2 = False
                break
        return found_no_free_overlap_route_1 or found_no_free_overlap_route_2

    def free_route(self, route):
        self.overlap_controller.free_overlap_of_route(route)

    async def reserve_route(self, route):
        segments = route.get_segments_of_route()
        for track_base_id in segments:
            track = self.tracks[track_base_id]
            for segment_id in segments[track_base_id]:
                print(f"--- Set track {segment_id} reserved")
                track.state[segment_id] = "reserved"
        return await self.overlap_controller.reserve_overlap_of_route(route)

    async def occupy_segment_of_track(self, track, segment_id):
        if track.state[segment_id] != "occupied":
            print(f"--- Set track {segment_id} occupied")
            track.state[segment_id] = "occupied"

            # Set signal to halt
            success_first_signal = True
            success_second_signal = True
            pos_of_segment = track.get_position_of_segment(segment_id)
            if pos_of_segment > 0:
                previous_signal = track.signals[pos_of_segment - 1]
                if previous_signal.yaramo_signal.direction == SignalDirection.IN:
                    success_first_signal = await self.signal_controller.set_signal_halt(previous_signal)
            if pos_of_segment < len(track.signals):
                next_signal = track.signals[pos_of_segment]
                if next_signal.yaramo_signal.direction == SignalDirection.GEGEN:
                    success_second_signal = await self.signal_controller.set_signal_halt(next_signal)
            return success_first_signal and success_second_signal
        return True

    def free_segment_of_track(self, track, segment_id):
        if track.state[segment_id] != "free":
            print(f"--- Set track {segment_id} free")
            track.state[segment_id] = "free"

            # Free point
            pos_of_segment = track.get_position_of_segment(segment_id)
            if pos_of_segment == 0 or pos_of_segment == len(track.signals) + 1:
                route = None
                for active_route in self.interlocking.active_routes:
                    if active_route.contains_segment(segment_id):
                        route = active_route
                        break
                if route is None:
                    raise ValueError("Active route not found")

                driving_direction = route.get_driving_direction_of_track_on_route(track)

                if pos_of_segment == 0 and driving_direction == "in":
                    self.point_controller.set_point_free(track.left_point)
                elif pos_of_segment == len(track.signals) + 1 and driving_direction == "gegen":
                    self.point_controller.set_point_free(track.right_point)

    def print_state(self):
        print("State of Tracks:")
        for base_track_id in self.tracks:
            track = self.tracks[base_track_id]
            for segment in track.state:
                print(f"{segment}: {track.state[segment]}")
