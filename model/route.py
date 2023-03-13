
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

    def to_string(self):
        return f"{self.start_signal.id} -> { self.end_signal.id}"
