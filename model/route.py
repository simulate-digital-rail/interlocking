
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
            return self.start_signal.wirkrichtung

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
        if self.end_signal.wirkrichtung == "in":
            return f"{last_track.base_track_id}-{pos_of_signal}"
        return f"{last_track.base_track_id}-{pos_of_signal+1}"

    def get_points_of_route(self):
        result = set()
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

    def get_max_speed_of_route(self):
        max_speed = -1
        for track in self.tracks:
            max_speed = max(max_speed, track.yaramo_edge.maximum_speed)
        return max_speed

    def to_string(self):
        return f"{self.start_signal.id} -> { self.end_signal.id}"
