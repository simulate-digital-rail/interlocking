import asyncio
import logging


class PointController(object):

    def __init__(self, infrastructure_providers, settings):
        self.points = None
        self.infrastructure_providers = infrastructure_providers
        self.settings = settings

    def reset(self):
        for point_id in self.points:
            self.points[point_id].orientation = "undefined"
            self.set_point_free(self.points[point_id])

    async def set_route(self, route):
        tasks = []
        point_orientations = route.get_necessary_point_orientations()
        for i in range(0, len(point_orientations), self.settings.max_number_of_points_at_same_time):
            async with asyncio.TaskGroup() as tg:
                for point_orientation in point_orientations[i:i+self.settings.max_number_of_points_at_same_time]:
                    point = point_orientation[0]
                    orientation = point_orientation[1]
                    if orientation == "left" or orientation == "right":
                        self.set_point_reserved(point)
                        tasks.append(tg.create_task(self.turn_point(point, orientation)))
                    else:
                        raise ValueError("Turn should happen but is not possible")

        return all(list(map(lambda task: task.result(), tasks)))

    def can_route_be_set(self, route):
        for point in route.get_points_of_route():
            if point.state != "free":
                return False
        return True

    def do_two_routes_collide(self, route_1, route_2):
        points_of_route_1 = route_1.get_points_of_route()
        points_of_route_2 = route_2.get_points_of_route()
        return len(points_of_route_1.intersection(points_of_route_2)) > 0

    async def turn_point(self, point, orientation):
        if point.orientation == orientation:
            # Everything is fine
            return True
        logging.info(f"--- Move point {point.point_id} to {orientation}")
        # tasks = []
        results = []
        for infrastructure_provider in self.infrastructure_providers:
            results.append(await infrastructure_provider.turn_point(point.yaramo_node, orientation))

        # async with asyncio.TaskGroup() as tg:
        #    for infrastructure_provider in self.infrastructure_providers:
        #        tasks.append(tg.create_task(infrastructure_provider.turn_point(point.yaramo_node, orientation)))
        # if all(list(map(lambda task: task.result(), tasks))):
        if all(results):
            point.orientation = orientation
            return True
        else:
            # TODO: Incident
            return False

    def set_point_reserved(self, point):
        logging.info(f"--- Set point {point.point_id} to reserved")
        point.state = "reserved"

    def set_point_free(self, point):
        logging.info(f"--- Set point {point.point_id} to free")
        point.state = "free"

    def reset_route(self, route):
        for point in route.get_points_of_route():
            self.set_point_free(point)

    def print_state(self):
        logging.debug("State of Points:")
        for point_id in self.points:
            point = self.points[point_id]
            logging.debug(f"{point.point_id}: {point.state} (Orientation: {point.orientation})")
