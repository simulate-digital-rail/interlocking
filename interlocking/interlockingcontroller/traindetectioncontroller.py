class TrainDetectionController(object):

    def __init__(self, track_controller, infrastructure_providers):
        self.track_controller = track_controller
        self.state = dict()
        for infrastructure_provider in infrastructure_providers:
            infrastructure_provider._set_tds_count_in_callback(self.count_in)
            infrastructure_provider._set_tds_count_out_callback(self.count_out)

    def count_in(self, track_segment_id, train_id: str):
        if track_segment_id not in self.state:
            self.state[track_segment_id] = 0
        self.state[track_segment_id] = self.state[track_segment_id] + 1
        self.track_controller.occupy_segment_of_track(self.get_segment_by_segment_id(track_segment_id), train_id)

    def count_out(self, track_segment_id, train_id: str):
        if track_segment_id not in self.state:
            raise ValueError("Train removed from non existing track")
        self.state[track_segment_id] = self.state[track_segment_id] - 1
        if self.state[track_segment_id] == 0:
            self.track_controller.free_segment_of_track(self.get_segment_by_segment_id(track_segment_id), train_id)

    def reset_track_segments_of_route(self, route):
        for track_segment_id in route.get_segments_of_route():
            self.state[track_segment_id] = 0

    def get_segment_by_segment_id(self, segment_id):
        if segment_id.endswith("-re"):
            segment_id = segment_id[:-3]
        for track_id in self.track_controller.tracks:
            track = self.track_controller.tracks[track_id]
            for segment in track.segments:
                if segment.segment_id == segment_id:
                    return segment
        return None
