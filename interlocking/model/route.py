from .overlap import Overlap
from yaramo.model import SignalDirection
import logging


class Route(object):

    def __init__(self, yaramo_route):
        self.yaramo_route = yaramo_route
        self.id = f"route_{yaramo_route.start_signal.name.upper()}-{yaramo_route.end_signal.name.upper()}"
        self.start_signal = None
        self.end_signal = None
        self.tracks = []
        self.overlap = None

    def contains_segment(self, segment_id):
        for track in self.tracks:
            if segment_id in track.state:
                return track
        return None

    def get_driving_direction_of_track_on_route(self, track):
        if len(self.tracks) == 0:
            raise ValueError("Route without tracks")
        if self.tracks[0].base_track_id == track.base_track_id:
            return str(self.start_signal.yaramo_signal.direction).lower()

        for i in range(1, len(self.tracks)):
            cur_track = self.tracks[i]

            if cur_track.base_track_id == track.base_track_id:
                prev_track = self.tracks[i - 1]
                if cur_track.left_point.point_id == prev_track.left_point.point_id or \
                   cur_track.left_point.point_id == prev_track.right_point.point_id:
                    return "in"
                elif cur_track.right_point.point_id == prev_track.left_point.point_id or \
                     cur_track.right_point.point_id == prev_track.right_point.point_id:
                    return "gegen"
                else:
                    raise ValueError("Tracks in Route not connected by point")
        raise ValueError("Route does not contain track")

    def get_last_segment_of_route(self):
        last_track = self.tracks[-1]
        pos_of_signal = last_track.get_position_of_signal(self.end_signal)
        if pos_of_signal == -1:
            raise ValueError("End signal not on last track")
        if self.end_signal.yaramo_signal.direction == SignalDirection.IN:
            return f"{last_track.base_track_id}-{pos_of_signal}"
        return f"{last_track.base_track_id}-{pos_of_signal+1}"

    def get_points_of_route(self):
        result = set()
        for i in range(0, len(self.tracks) - 1):
            first_track = self.tracks[i]
            second_track = self.tracks[i + 1]
            
            if first_track.left_point.does_point_connect_tracks(first_track, second_track):
                point = first_track.left_point
            elif first_track.right_point.does_point_connect_tracks(first_track, second_track):
                point = first_track.right_point
            else:
                raise ValueError("Two tracks have no common point")

            result.add(point)
        return result

    def get_necessary_point_orientations(self):
        result = []
        for i in range(0, len(self.tracks) - 1):
            first_track = self.tracks[i]
            second_track = self.tracks[i + 1]

            point = None
            if first_track.left_point.does_point_connect_tracks(first_track, second_track):
                point = first_track.left_point
            elif first_track.right_point.does_point_connect_tracks(first_track, second_track):
                point = first_track.right_point
            else:
                raise ValueError("Two tracks have no common point")

            result.append((point, point.get_necessary_orientation(first_track, second_track)))
        return result

    def get_segments_of_route(self):
        result = dict()

        if self.start_signal.track.base_track_id == self.end_signal.track.base_track_id:
            # Start signal and end signal are on the same track
            pos_start_signal = self.start_signal.track.get_position_of_signal(self.start_signal)
            pos_end_signal = self.end_signal.track.get_position_of_signal(self.end_signal)
            result[self.start_signal.track.base_track_id] = self.start_signal\
                .track.get_segments_of_range(pos_start_signal + 1, pos_end_signal + 1)
        else:
            result[self.start_signal.track.base_track_id] = self.start_signal.track.\
                get_segments_from_signal(self.start_signal)
            for i in range(1, len(self.tracks) - 1):
                result[self.tracks[i].base_track_id] = self.tracks[i].get_all_segments_of_track()
            result[self.end_signal.track.base_track_id] = self.end_signal.track.\
                get_segments_to_signal(self.end_signal)
        return result

    def get_overlaps_of_route(self):
        max_speed = self.yaramo_route.maximum_speed
        if max_speed <= 30:
            missing_length_of_overlap = 0
        elif max_speed <= 40:
            missing_length_of_overlap = 50
        elif max_speed <= 60:
            missing_length_of_overlap = 100
        else:
            missing_length_of_overlap = 200

        overlap_obj = Overlap(missing_length_of_overlap, self)
        if missing_length_of_overlap == 0:
            return [overlap_obj]

        last_track = self.end_signal.track
        segments_from_end_signal = last_track.get_segments_from_signal(self.end_signal)

        for segment_id in segments_from_end_signal:
            overlap_obj.add_segment(last_track, segment_id)
            if overlap_obj.is_full():
                return [overlap_obj]

        # Current track is not enough
        found_overlaps = self.get_overlaps_of_route_recursive(last_track, self.end_signal.yaramo_signal.direction,
                                                              overlap_obj)
        full_overlaps = []
        longest_overlap = found_overlaps[0]
        for overlap in found_overlaps:
            if overlap.is_full():
                full_overlaps.append(overlap)
            if overlap.missing_length < longest_overlap.missing_length:
                longest_overlap = overlap
        if len(full_overlaps) > 0:
            return full_overlaps
        logging.warning("--- Warning: No full overlap found, take the longest one")
        return [longest_overlap]

    def get_overlaps_of_route_recursive(self, cur_track, cur_driving_direction, cur_overlap):
        if cur_driving_direction == SignalDirection.IN:
            next_point = cur_track.right_point
        else:
            next_point = cur_track.left_point
        cur_overlap.points.append(next_point)
        successors = next_point.get_possible_successors(cur_track)
        if len(successors) == 0:
            return [cur_overlap]
        results = []
        for successor_track in successors:
            new_overlap = cur_overlap.duplicate()
            driving_direction = SignalDirection.IN
            if successor_track.right_point.point_id == next_point.point_id:
                driving_direction = SignalDirection.GEGEN
            if driving_direction == SignalDirection.IN:
                for segment_id in successor_track.lengths:
                    new_overlap.add_segment(successor_track, segment_id)
                    if new_overlap.is_full():
                        break
            else:
                for segment_id in reversed(successor_track.lengths):
                    new_overlap.add_segment(successor_track, segment_id)
                    if new_overlap.is_full():
                        break
            results.append(new_overlap)
            if not new_overlap.is_full():
                # Track was not long enough
                results.extend(self.get_overlaps_of_route_recursive(successor_track, driving_direction, new_overlap))
        return results

    def to_string(self):
        return f"{self.start_signal.yaramo_signal.name} -> { self.end_signal.yaramo_signal.name}"
