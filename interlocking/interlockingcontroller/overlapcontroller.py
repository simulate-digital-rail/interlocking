import asyncio
import logging


class OverlapController(object):

    def __init__(self, interlocking, track_controller, point_controller):
        self.interlocking = interlocking
        self.track_controller = track_controller
        self.point_controller = point_controller

    async def reserve_overlap_of_route(self, route):
        overlap = self.get_first_reservable_overlap(route)
        if overlap is None:
            raise ValueError("No reservable overlap found")
        self.reserve_segments_of_overlap(overlap)
        success = await self.reserve_points_of_overlap(overlap)
        route.overlap = overlap
        return success

    def get_first_reservable_overlap(self, route):
        all_overlaps = route.get_overlaps_of_route()
        for overlap in all_overlaps:
            if self.can_overlap_be_reserved(overlap):
                return overlap
        return None

    def can_overlap_be_reserved(self, overlap):
        for track in overlap.segments:
            for segment_id in overlap.segments[track]:
                if track.state[segment_id] != "free" and track.state[segment_id] != "reserved-overlap":
                    return False
        for point in overlap.points:
            if point.state != "free" and point.state != "reserved-overlap":
                return False
        return True

    def can_any_overlap_be_reserved(self, route):
        return self.get_first_reservable_overlap(route) is not None

    def reserve_segments_of_overlap(self, overlap):
        for track in overlap.segments:
            for segment_id in overlap.segments[track]:
                logging.info(f"--- Set track {segment_id} reserved (overlap)")
                track.state[segment_id] = "reserved-overlap"

    async def reserve_points_of_overlap(self, overlap):
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for point in overlap.points:
                logging.info(f"--- Set point {point.point_id} to reserved (overlap)")
                point.state = "reserved-overlap"

                # Get necessary orientation
                points_tracks = [point.head, point.left, point.right]
                found_tracks = []
                for track in points_tracks:
                    if track in overlap.segments:
                        found_tracks.append(track)

                if len(found_tracks) != 2:
                    raise ValueError("Overlap contains points without 2 of their tracks")
                necessery_orientation = point.get_necessary_orientation(found_tracks[0], found_tracks[1])
                tasks.append(tg.create_task(self.point_controller.turn_point(point, necessery_orientation)))
        return all(list(map(lambda task: task.result(), tasks)))

    def free_overlap_of_route(self, route):
        overlap = route.overlap
        if overlap is None:
            raise ValueError("Overlap is None")
        self.free_segments_of_overlap(overlap, route)
        self.free_points_of_overlap(overlap, route)

    def free_segments_of_overlap(self, overlap, route):
        for track in overlap.segments:
            for segment_id in overlap.segments[track]:
                if not self.is_segment_used_in_any_other_overlap(segment_id, route):
                    logging.info(f"--- Set track {segment_id} free")
                    track.state[segment_id] = "free"

    def free_points_of_overlap(self, overlap, route):
        for point in overlap.points:
            if not self.is_point_used_in_any_other_overlap(point, route):
                self.point_controller.set_point_free(point)

    def is_segment_used_in_any_other_overlap(self, segment_id, route):
        for active_route in self.interlocking.active_routes:
            if active_route.id != route.id:
                overlap_of_active_route = active_route.overlap
                if overlap_of_active_route is None:
                    raise ValueError("An active route has no overlap object")
                for track in overlap_of_active_route.segments:
                    if segment_id in overlap_of_active_route.segments[track]:
                        return True
        return False

    def is_point_used_in_any_other_overlap(self, point, route):
        for active_route in self.interlocking.active_routes:
            if active_route.id != route.id:
                overlap_of_active_route = active_route.overlap
                if overlap_of_active_route is None:
                    raise ValueError("An active route has no overlap object")
                for point_of_active_route in overlap_of_active_route.points:
                    if point.point_id == point_of_active_route.point_id:
                        return True
        return False
