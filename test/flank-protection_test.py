# Example 1: Halt zeigendes Signal
# Example 2: Schutzweiche
# Example 3: Schutztransportweiche mit Schutzweise und halt zeigendem Signal

#from .helper import get_topology_from_planpro_file
import logging

import helper
from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import LoggingInfrastructureProvider, InfrastructureProvider
from interlocking.model import OccupancyState
from interlocking.model.helper import Settings
import asyncio


class TrackOperationsInfrastructureProvider(InfrastructureProvider):
    def __init__(self):
        super().__init__()
        self.point_operations = set()
        self.signal_operations = set()

    async def set_signal_aspect(self, yaramo_signal, target_aspect):
        self.signal_operations.add((yaramo_signal, target_aspect))
        return True

    async def turn_point(self, yaramo_point, target_orientation: str):
        self.point_operations.add((yaramo_point, target_orientation))
        return True

    def was_signal_set_to_aspect(self, yaramo_signal, aspect):
        for signal_operation in self.signal_operations:
            if signal_operation[0].name == yaramo_signal.name and signal_operation[1] == aspect:
                return True
        return False


def test_example_1():
    topology = helper.get_topology_from_planpro_file("./flank-protection-example1.ppxml")
    track_operations_ip = TrackOperationsInfrastructureProvider()
    infrastructure_provider = [LoggingInfrastructureProvider(), track_operations_ip]

    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3))
    interlocking.prepare(topology)
    route = helper.get_route_by_signal_names(topology, "99N1", "99N2")
    asyncio.run(helper.set_route(interlocking, route, True, "RB101"))
    interlocking.print_state()

    # Test point is in correct position
    point_id = "fe8ed"  # point on the route between 99N1 and 99N2
    point = interlocking.point_controller.points[point_id]
    assert "RB101" in point.used_by
    assert point.orientation == "left"
    assert point.state == OccupancyState.RESERVED

    flank_protection_signal = helper.get_interlocking_signal_by_name(interlocking, "99N3")
    assert flank_protection_signal.signal_aspect == "halt"
    assert track_operations_ip.was_signal_set_to_aspect(flank_protection_signal.yaramo_signal, "halt")
    assert flank_protection_signal.state == OccupancyState.FLANK_PROTECTION
    assert "RB101" in flank_protection_signal.used_by


def test_example_2():
    topology = helper.get_topology_from_planpro_file("./flank-protection-example2.ppxml")
    track_operations_ip = TrackOperationsInfrastructureProvider()
    infrastructure_provider = [LoggingInfrastructureProvider(), track_operations_ip]

    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3))
    interlocking.prepare(topology)
    route = helper.get_route_by_signal_names(topology, "60E1", "60A1")
    asyncio.run(helper.set_route(interlocking, route, True, "RB101"))
    interlocking.print_state()

    # Test point is in correct position
    point_id = "7a7f9"  # point on the route between 60BS2 and 60BS3
    point = interlocking.point_controller.points[point_id]
    assert "RB101" in point.used_by
    assert point.orientation == "left"
    assert point.state == OccupancyState.RESERVED

    flank_protection_point_id = "aed72"
    flank_protection_point = interlocking.point_controller.points[flank_protection_point_id]
    assert flank_protection_point.orientation == "left"
    assert flank_protection_point.state == OccupancyState.FLANK_PROTECTION
    assert "RB101" in flank_protection_point.used_by


def test_example_3():
    topology = helper.get_topology_from_planpro_file("./flank-protection-example3.ppxml")
    track_operations_ip = TrackOperationsInfrastructureProvider()
    infrastructure_provider = [LoggingInfrastructureProvider(), track_operations_ip]

    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3))
    interlocking.prepare(topology)
    route = helper.get_route_by_signal_names(topology, "60E1", "60A1")
    asyncio.run(helper.set_route(interlocking, route, True, "RB101"))
    interlocking.print_state()

    # Test point is in correct position
    point_id = "e40a7"  # point on the route between 60N1 and 60N2
    point = interlocking.point_controller.points[point_id]
    assert "RB101" in point.used_by
    assert point.orientation == "right"
    assert point.state == OccupancyState.RESERVED

    flank_protection_transport_point_id = "8fc1f"  # n3
    flank_protection_transport_point = interlocking.point_controller.points[flank_protection_transport_point_id]
    assert flank_protection_transport_point.state == OccupancyState.FLANK_PROTECTION_TRANSPORT
    assert "RB101" in flank_protection_transport_point.used_by

    flank_protection_point_id = "da301"  # n6
    flank_protection_point = interlocking.point_controller.points[flank_protection_point_id]
    assert point.orientation == "right"
    assert flank_protection_point.state == OccupancyState.FLANK_PROTECTION
    assert "RB101" in flank_protection_point.used_by

    flank_protection_signal = helper.get_interlocking_signal_by_name(interlocking, "60E2")
    assert flank_protection_signal.signal_aspect == "halt"
    assert track_operations_ip.was_signal_set_to_aspect(flank_protection_signal.yaramo_signal, "halt")
    assert flank_protection_signal.state == OccupancyState.FLANK_PROTECTION
    assert "RB101" in flank_protection_signal.used_by


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_example_1()
    test_example_2()
    test_example_3()

