from interlocking.model import OccupancyState


class OverlapController(object):

    def __init__(self, interlocking, track_controller, point_controller):
        self.interlocking = interlocking
        self.track_controller = track_controller
        self.point_controller = point_controller

    def reserve_overlap_of_route(self, route, train_id: str):
        overlap = self.get_first_reservable_overlap(route, train_id)
        if overlap is None:
            raise ValueError("No reservable overlap found")
        self.reserve_segments_of_overlap(overlap, train_id)
        self.reserve_points_of_overlap(overlap, train_id)
        route.overlap = overlap

    def get_first_reservable_overlap(self, route, train_id: str):
        all_overlaps = route.get_overlaps_of_route()
        for overlap in all_overlaps:
            if self.can_overlap_be_reserved(overlap, train_id):
                return overlap
        return None

    def can_overlap_be_reserved(self, overlap, train_id: str):
        for segment in overlap.segments:
            if segment.state == OccupancyState.FREE:
                continue
            if segment.state == OccupancyState.RESERVED_OVERLAP and segment.is_only_used_by_train(train_id):
                continue
            return False
        for point in overlap.points:
            if point.state == OccupancyState.FREE:
                continue
            if point.state == OccupancyState.RESERVED_OVERLAP and point.is_only_used_by_train(train_id):
                continue
            return False
        return True

    def can_any_overlap_be_reserved(self, route, train_id: str):
        return self.get_first_reservable_overlap(route, train_id) is not None

    def reserve_segments_of_overlap(self, overlap, train_id: str):
        for segment in overlap.segments:
            print(f"--- Set track {segment.segment_id} reserved (overlap)")
            segment.state = OccupancyState.RESERVED_OVERLAP
            segment.used_by.add(train_id)

    def reserve_points_of_overlap(self, overlap, train_id: str):
        for point in overlap.points:
            print(f"--- Set point {point.point_id} to reserved (overlap)")
            point.state = OccupancyState.RESERVED_OVERLAP
            point.used_by.add(train_id)

            if point.is_point:
                # Get necessary orientation
                points_tracks = [point.head, point.left, point.right]
                found_tracks = []
                for track in points_tracks:
                    if track in set(map(lambda seg: seg.track, overlap.segments)):
                        found_tracks.append(track)

                if len(found_tracks) != 2:
                    raise ValueError("Overlap contains points without 2 of their tracks")
                necessery_orientation = point.get_necessary_orientation(found_tracks[0], found_tracks[1])
                self.point_controller.turn_point(point, necessery_orientation)

    def free_overlap_of_route(self, route, train_id: str):
        overlap = route.overlap
        if overlap is None:
            raise ValueError("Overlap is None")
        self.free_segments_of_overlap(overlap, route, train_id)
        self.free_points_of_overlap(overlap, route, train_id)

    def free_segments_of_overlap(self, overlap, route, train_id: str):
        for segment in overlap.segments:
            if not self.is_segment_used_in_any_other_overlap(segment, route) and \
                    segment.state == OccupancyState.RESERVED_OVERLAP:
                print(f"--- Set track {segment.segment_id} free")
                segment.state = OccupancyState.FREE
                segment.used_by.remove(train_id)

    def free_points_of_overlap(self, overlap, route, train_id: str):
        for point in overlap.points:
            if not self.is_point_used_in_any_other_overlap(point, route) and \
                    point.state == OccupancyState.RESERVED_OVERLAP:
                self.point_controller.set_point_free(point, train_id)

    def is_segment_used_in_any_other_overlap(self, segment, route):
        for active_route in self.interlocking.active_routes:
            if active_route.id != route.id:
                overlap_of_active_route = active_route.overlap
                if overlap_of_active_route is None:
                    raise ValueError("An active route has no overlap object")
                if segment.segment_id in set(map(lambda seg: seg.segment_id, overlap_of_active_route.segments)):
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
