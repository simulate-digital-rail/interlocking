from interlocking.model import OccupancyState


class PointController(object):

    def __init__(self, infrastructure_providers):
        self.points = None
        self.infrastructure_providers = infrastructure_providers

    def reset(self):
        for point_id in self.points:
            self.points[point_id].orientation = "undefined"
            self.set_point_free(self.points[point_id])

    def set_route(self, route):
        for point_orientations in route.get_necessary_point_orientations():
            point = point_orientations[0]
            orientation = point_orientations[1]
            if orientation == "left" or orientation == "right":
                self.turn_point(point, orientation)
                self.set_point_reserved(point)
            else:
                raise ValueError("Turn should happen but is not possible")

    def can_route_be_set(self, route):
        for point in route.get_points_of_route():
            if point.state != OccupancyState.FREE:
                return False
        return True

    def do_two_routes_collide(self, route_1, route_2):
        points_of_route_1 = route_1.get_points_of_route()
        points_of_route_2 = route_2.get_points_of_route()
        return len(points_of_route_1.intersection(points_of_route_2)) > 0

    def turn_point(self, point, orientation):
        if point.orientation == orientation:
            # Everything is fine
            return
        print(f"--- Move point {point.point_id} to {orientation}")
        point.orientation = orientation
        for infrastructure_provider in self.infrastructure_providers:
            infrastructure_provider.turn_point(point.yaramo_node, orientation)

    def set_point_reserved(self, point):
        print(f"--- Set point {point.point_id} to reserved")
        point.state = OccupancyState.RESERVED

    def set_point_free(self, point):
        print(f"--- Set point {point.point_id} to free")
        point.state = OccupancyState.FREE

    def reset_route(self, route):
        for point in route.get_points_of_route():
            self.set_point_free(point)

    def print_state(self):
        print("State of Points:")
        for point_id in self.points:
            point = self.points[point_id]
            print(f"{point.point_id}: {point.state} (Orientation: {point.orientation})")
