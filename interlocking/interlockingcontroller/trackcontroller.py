from .overlapcontroller import OverlapController
from interlocking.model import OccupancyState, Route
from yaramo.model import SignalDirection
import logging


class TrackController(object):

    def __init__(self, interlocking, point_controller, signal_controller):
        self.tracks = {}
        self.interlocking = interlocking
        self.point_controller = point_controller
        self.signal_controller = signal_controller
        self.overlap_controller = OverlapController(interlocking, self, self.point_controller)

    def reset(self):
        for base_track_id in self.tracks:
            track = self.tracks[base_track_id]
            for segment in track.segments:
                segment.state = OccupancyState.FREE
                segment.used_by = set()

    async def set_route(self, route, train_id: str):
        return await self.reserve_route(route, train_id)

    def can_route_be_set(self, route, train_id: str):
        for segment in route.get_segments_of_route():
            if segment.state == OccupancyState.FREE:
                continue
            if segment.is_only_used_by_train(train_id):
                continue
            print(f"{segment.segment_id} is used by other train")
            return False
        return self.overlap_controller.can_any_overlap_be_reserved(route, train_id)

    def do_two_routes_collide(self, route_1: Route, route_2: Route):
        segments_of_route_1 = set(map(lambda seg: seg.segment_id, route_1.get_segments_of_route()))
        segments_of_route_2 = set(map(lambda seg: seg.segment_id, route_2.get_segments_of_route()))
        if len(segments_of_route_1.intersection(segments_of_route_2)) > 0:
            return True

        overlaps_of_route_1 = route_1.get_overlaps_of_route()
        no_non_colliding_overlap_for_route_1 = True
        if len(overlaps_of_route_1) > 0:
            for overlap in overlaps_of_route_1:
                overlap_segments = set(map(lambda seg: seg.segment_id, overlap.segments))
                if len(overlap_segments.intersection(segments_of_route_2)) == 0:  # Non-colliding overlap found
                    no_non_colliding_overlap_for_route_1 = False
                    break
        else:
            # No overlap necessary, so assume that there is non-colliding overlap
            no_non_colliding_overlap_for_route_1 = False

        overlaps_of_route_2 = route_2.get_overlaps_of_route()
        no_non_colliding_overlap_for_route_2 = True
        if len(overlaps_of_route_2) > 0:
            for overlap in overlaps_of_route_2:
                overlap_segments = set(map(lambda seg: seg.segment_id, overlap.segments))
                if len(overlap_segments.intersection(segments_of_route_1)) == 0:  # Non-colliding overlap found
                    no_non_colliding_overlap_for_route_2 = False
                    break
        else:
            # No overlap necessary, so assume that there is non-colliding overlap
            no_non_colliding_overlap_for_route_2 = False
        return no_non_colliding_overlap_for_route_1 or no_non_colliding_overlap_for_route_2

    def free_route(self, route, train_id: str):
        for segment in route.get_segments_of_route():
            if segment.state != OccupancyState.FREE:
                logging.error(f"You are freeing a route where at least one segment is not free "
                              f"(segment id: {segment.segment_id})")
        self.overlap_controller.free_overlap_of_route(route, train_id)

    def reset_route(self, route, train_id: str):
        for segment in route.get_segments_of_route():
            if segment.state != OccupancyState.FREE:
                logging.info(f"--- Set track {segment.segment_id} free")
                segment.state = OccupancyState.FREE
                segment.used_by.remove(train_id)
        self.overlap_controller.free_overlap_of_route(route, train_id)

    async def reserve_route(self, route, train_id: str):
        for segment in route.get_segments_of_route():
            logging.info(f"--- Set track {segment.segment_id} reserved")
            segment.state = OccupancyState.RESERVED
            segment.used_by.add(train_id)
        return await self.overlap_controller.reserve_overlap_of_route(route, train_id)

    async def occupy_segment_of_track(self, segment, train_id: str):
        if segment.state != OccupancyState.OCCUPIED:
            logging.info(f"--- Set track {segment.segment_id} occupied")
            segment.state = OccupancyState.OCCUPIED
            if train_id not in segment.used_by:
                raise ValueError(f"Train {train_id} is using a segment, which wasn't reserved before.")

            # Set signal to halt
            success_first_signal = True
            success_second_signal = True
            pos_of_segment = segment.track.get_position_of_segment(segment)

            if pos_of_segment > 0:
                previous_signal = segment.track.signals[pos_of_segment - 1]
                if previous_signal.yaramo_signal.direction == SignalDirection.IN:
                    success_first_signal = await self.signal_controller.set_signal_halt(previous_signal)
            if pos_of_segment < len(segment.track.signals):
                next_signal = segment.track.signals[pos_of_segment]
                if next_signal.yaramo_signal.direction == SignalDirection.GEGEN:
                    success_second_signal = await self.signal_controller.set_signal_halt(next_signal)
            return success_first_signal and success_second_signal
        return True

    def free_segment_of_track(self, segment, train_id: str):
        if segment.state != OccupancyState.FREE:
            logging.info(f"--- Set track {segment.segment_id} free")
            segment.state = OccupancyState.FREE
            segment.used_by.remove(train_id)

            # Free point
            track = segment.track
            if track.is_first_segment(segment) or track.is_last_segment(segment):
                route = None
                for active_route in self.interlocking.active_routes:
                    if active_route.contains_segment(segment):
                        route = active_route
                        break
                if route is None:
                    raise ValueError("Active route not found")

                driving_direction = route.get_driving_direction_of_track_on_route(segment.track)

                if track.is_first_segment(segment) and driving_direction == "in" and \
                        segment.track.left_point.state != OccupancyState.FREE:
                    # The occupancy state of the previous point can be free, when the train starts on this segment
                    self.point_controller.set_point_free(segment.track.left_point, train_id)
                elif track.is_last_segment(segment) and driving_direction == "gegen" and \
                        segment.track.right_point.state != OccupancyState.FREE:
                    self.point_controller.set_point_free(segment.track.right_point, train_id)

    def print_state(self):
        logging.debug("State of Tracks:")
        for base_track_id in self.tracks:
            track = self.tracks[base_track_id]
            for segment in track.segments:
                logging.debug(f"{segment.segment_id}: {segment.state} (used by: {segment.used_by})")
