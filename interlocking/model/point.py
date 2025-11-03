from yaramo.model import EdgeConnectionDirection
from .occupancystate import OccupancyState
from .track import Track


class Point(object):

    def __init__(self, yaramo_node):
        self.yaramo_node = yaramo_node
        self.point_id = self.yaramo_node.uuid[-5:]
        self.orientation = "undefined"  # either left, right or undefined
        self.state = OccupancyState.FREE
        self.used_by = set()  # If point is reserved, occupied or part of an overlap, this contains the train numbers.
        self.is_used_for_flank_protection = False
        self.head = None
        self.left = None
        self.right = None

    def connect_track(self, track):
        if not self.yaramo_node.is_point():
            self.head = track
            return

        connection_direction = self.yaramo_node.get_anschluss_for_edge(track.yaramo_edge)

        if connection_direction == EdgeConnectionDirection.Spitze:
            self.head = track
        elif connection_direction == EdgeConnectionDirection.Links:
            self.left = track
        elif connection_direction == EdgeConnectionDirection.Rechts:
            self.right = track

        #connection_directions = self.yaramo_node.get_anschluss_of_other(other_node)
        #for connection_direction in connection_directions:
        #    if connection_direction == NodeConnectionDirection.Spitze:
        #        self.head = track
        #    elif connection_direction == NodeConnectionDirection.Links:
        #        self.left = track
        #    elif connection_direction == NodeConnectionDirection.Rechts:
        #        self.right = track

    def is_only_used_by_train(self, train_id: str):
        return len(self.used_by) == 1 and train_id in self.used_by

    def is_track_connected(self, track):
        all_base_ids = []
        if self.head is not None:
            all_base_ids.append(self.head.base_track_id)
        if self.left is not None:
            all_base_ids.append(self.left.base_track_id)
        if self.right is not None:
            all_base_ids.append(self.right.base_track_id)
        return track.base_track_id in all_base_ids

    def does_point_connect_tracks(self, track_1, track_2):
        if not self.yaramo_node.is_point():
            return False
        if track_1 is None or track_2 is None:
            return False
        if track_1.base_track_id == track_2.base_track_id:
            return False

        return self.is_track_connected(track_1) and self.is_track_connected(track_2)

    def get_necessary_orientation(self, track_1, track_2):
        if track_1 is None or track_2 is None or track_1.base_track_id == track_2.base_track_id:
            raise ValueError("Necessary Orientation is not definable. Either a given track is None or they are equal")
        if not self.is_track_connected(track_1) or not self.is_track_connected(track_2):
            raise ValueError("Necessary Orientation is not definable. A given track is not connected")

        if self.head.base_track_id == track_1.base_track_id:
            if self.left.base_track_id == track_2.base_track_id:
                return "left"
            return "right"
        elif self.head.base_track_id == track_2.base_track_id:
            if self.left.base_track_id == track_1.base_track_id:
                return "left"
            return "right"
        raise ValueError("None of the given edges is the head edge, orientation not possible")

    def get_connection_direction_of_track(self, track: Track) -> EdgeConnectionDirection:
        if self.head.base_track_id == track.base_track_id:
            return EdgeConnectionDirection.Spitze
        if self.left.base_track_id == track.base_track_id:
            return EdgeConnectionDirection.Links
        if self.right.base_track_id == track.base_track_id:
            return EdgeConnectionDirection.Rechts
        raise ValueError("Given track is not connected to node")

    def get_possible_successors(self, track):
        if not self.yaramo_node.is_point():
            return []
        if self.head.base_track_id == track.base_track_id:
            return [self.left, self.right]
        if self.left.base_track_id == track.base_track_id or self.right.base_track_id == track.base_track_id:
            return [self.head]
        raise ValueError("Given track is no valid predecessor")
