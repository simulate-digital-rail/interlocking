from interlocking.model import OccupancyState, Point
from interlocking.model.helper import Settings
from interlocking.infrastructureprovider import InfrastructureProvider
from .flankprotectioncontroller import FlankProtectionController
from .signalcontroller import SignalController
import asyncio
import logging


class PointController(object):

    def __init__(self, signal_controller: SignalController, infrastructure_providers: list[InfrastructureProvider],
                 settings: Settings):
        self.points: dict[str, Point] = {}
        self.infrastructure_providers = infrastructure_providers
        self.settings = settings
        self.flank_protection_controller = FlankProtectionController(self, signal_controller)

    def reset(self):
        for point_id in self.points:
            self.points[point_id].orientation = "undefined"
            self.points[point_id].state = OccupancyState.FREE
            self.points[point_id].used_by = set()
        self.flank_protection_controller.reset()

    async def set_route(self, route, train_id: str):
        tasks = []
        point_orientations = route.get_necessary_point_orientations()
        for i in range(0, len(point_orientations), self.settings.max_number_of_points_at_same_time):
            async with asyncio.TaskGroup() as tg:
                for point_orientation in point_orientations[i:i+self.settings.max_number_of_points_at_same_time]:
                    point = point_orientation[0]
                    orientation = point_orientation[1]
                    if orientation == "left" or orientation == "right":
                        self.set_point_reserved(point, train_id)
                        tasks.append(tg.create_task(self.turn_point(point, orientation)))
                        tasks.append(tg.create_task(self.flank_protection_controller.add_flank_protection_for_point(point, orientation, route, train_id)))
                    else:
                        raise ValueError("Turn should happen but is not possible")

        return all(list(map(lambda task: task.result(), tasks)))

    def can_route_be_set(self, route, train_id: str):
        for point in route.get_points_of_route():
            if point.state == OccupancyState.FREE:
                continue
            if point.is_only_used_by_train(train_id):
                continue
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
        if point.is_used_for_flank_protection is True:
            logging.error(f"Can not turn point of point {point.point_id} to {orientation}, "
                          f"since it is used for flank protection.")
            return False
        logging.info(f"--- Move point {point.point_id} to {orientation}")
        # tasks = []
        results = []
        for infrastructure_provider in self.infrastructure_providers:
            results.append(await infrastructure_provider.call_turn_point(point.yaramo_node, orientation))

        # async with asyncio.TaskGroup() as tg:
        #    for infrastructure_provider in self.infrastructure_providers:
        #        tasks.append(tg.create_task(infrastructure_provider.call_turn_point(point.yaramo_node, orientation)))
        # if all(list(map(lambda task: task.result(), tasks))):
        if all(results):
            point.orientation = orientation
            return True
        else:
            # TODO: Incident
            return False

    def set_point_reserved(self, point, train_id: str):
        logging.info(f"--- Set point {point.point_id} to reserved")
        point.state = OccupancyState.RESERVED
        point.used_by.add(train_id)

    def set_point_free(self, point, train_id: str):
        if point.state != OccupancyState.FREE:
            logging.info(f"--- Set point {point.point_id} to free")
            point.state = OccupancyState.FREE
            point.used_by.remove(train_id)
            self.flank_protection_controller.free_flank_protection_of_point(point, point.orientation)

    def reset_route(self, route, train_id: str):
        for point in route.get_points_of_route():
            self.set_point_free(point, train_id)

    def print_state(self):
        logging.debug("State of Points:")
        for point_id in self.points:
            point = self.points[point_id]
            logging.debug(f"{point.point_id}: {point.state} (Orientation: {point.orientation}) "
                          f"(used by: {point.used_by}) (is used for FP: {point.is_used_for_flank_protection})")
