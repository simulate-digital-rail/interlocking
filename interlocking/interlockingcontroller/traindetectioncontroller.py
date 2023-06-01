class TrainDetectionController(object):

    def __init__(self, track_controller, infrastructure_providers):
        self.track_controller = track_controller
        self.state = dict()
        for infrastructure_provider in infrastructure_providers:
            infrastructure_provider._set_tds_count_in_callback(self.count_in)
            infrastructure_provider._set_tds_count_out_callback(self.count_out)

    async def count_in(self, track_segment_id):
        if track_segment_id not in self.state:
            self.state[track_segment_id] = 0
        self.state[track_segment_id] = self.state[track_segment_id] + 1
        return await self.track_controller.occupy_segment_of_track(self.get_track_of_segment_id(track_segment_id),
                                                                   track_segment_id)

    def count_out(self, track_segment_id):
        if track_segment_id not in self.state:
            raise ValueError("Train removed from non existing track")
        self.state[track_segment_id] = self.state[track_segment_id] - 1
        if self.state[track_segment_id] == 0:
            self.track_controller.free_segment_of_track(self.get_track_of_segment_id(track_segment_id),
                                                        track_segment_id)

    def get_track_of_segment_id(self, track_segment_id):
        for track_key in self.track_controller.tracks:
            track = self.track_controller.tracks[track_key]
            if track_segment_id in track.state:
                return track
