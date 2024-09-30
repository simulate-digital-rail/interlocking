from .helper import topologyhelper, interlockinghelper
from interlocking.model import OccupancyState
from interlocking.model.helper import IsRouteSetResult
from interlocking.infrastructureprovider import RandomWaitInfrastructureProvider
from yaramo.model import Route as YaramoRoute, Signal as YaramoSignal, Edge as YaramoEdge, Node as YaramoNode
import asyncio
import unittest


def test_reset():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    interlocking.print_state()
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")
    route_2.maximum_speed = 30  # Remove overlap from this route through the station
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB102"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "go", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)

    interlockinghelper.test_track(interlocking, "3a70a-0", "RB102", OccupancyState.RESERVED)
    interlockinghelper.test_signal(interlocking, "60ES2", "RB102", "go", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "fd73d", "RB102", "right", OccupancyState.RESERVED)

    assert len(interlocking.active_routes) == 2

    asyncio.run(interlocking.reset())

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "halt", OccupancyState.FREE)
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "undefined", OccupancyState.FREE)

    interlockinghelper.test_track(interlocking, "3a70a-0", "RB102", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60ES2", "RB102", "halt", OccupancyState.FREE)
    interlockinghelper.test_point(interlocking, "fd73d", "RB102", "undefined", OccupancyState.FREE)

    assert len(interlocking.active_routes) == 0


def test_print_state():
    # Tests if print state runs without error
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)
    interlocking.print_state()

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    interlocking.print_state()


def test_driving():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    interlockinghelper.test_track(interlocking, "b8e69-1", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "b8e69-2", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "go", OccupancyState.RESERVED)

    route_2 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB101"))

    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "fb749", "RB101", "right", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "e641b", "RB101", "right", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)

    # "Drive" some train
    ip = interlocking.infrastructure_providers[0]
    asyncio.run(ip.tds_count_in("de139-1", "RB101"))
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "halt", OccupancyState.RESERVED)
    asyncio.run(ip.tds_count_in("de139-2", "RB101"))
    asyncio.run(ip.tds_count_out("de139-1", "RB101"))
    asyncio.run(ip.tds_count_in("94742-0", "RB101"))
    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.OCCUPIED)
    asyncio.run(ip.tds_count_out("de139-2", "RB101"))
    asyncio.run(ip.tds_count_in("b8e69-0", "RB101"))
    asyncio.run(ip.tds_count_out("94742-0", "RB101"))
    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    asyncio.run(ip.tds_count_in("b8e69-1", "RB101"))
    asyncio.run(ip.tds_count_out("b8e69-0", "RB101"))
    interlockinghelper.free_route(interlocking, route_1, "RB101")

    asyncio.run(ip.tds_count_in("b8e69-2", "RB101"))
    asyncio.run(ip.tds_count_out("b8e69-1", "RB101"))
    asyncio.run(ip.tds_count_in("b8e69-3", "RB101"))
    asyncio.run(ip.tds_count_out("b8e69-2", "RB101"))
    asyncio.run(ip.tds_count_in("a8f44-0", "RB101"))
    asyncio.run(ip.tds_count_out("b8e69-3", "RB101"))
    asyncio.run(ip.tds_count_out("a8f44-0", "RB101"))
    interlockinghelper.free_route(interlocking, route_2, "RB101")

    # Verify flank protection cleanup
    signal_as1 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60AS1")
    assert not signal_as1.is_used_for_flank_protection
    signal_as4 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60AS1")
    assert not signal_as4.is_used_for_flank_protection
    point_fa9 = interlockinghelper.get_interlocking_point_by_id(interlocking, "fa9ea")
    assert not point_fa9.is_used_for_flank_protection
    point_21b = interlockinghelper.get_interlocking_point_by_id(interlocking, "21b88")
    assert not point_21b.is_used_for_flank_protection


def test_is_route_set():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")

    # Route set with correct train
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_SET_CORRECTLY

    # Route not set
    assert interlocking.is_route_set(route_2, "RB101") == IsRouteSetResult.ROUTE_NOT_SET

    # Route set with wrong train
    assert interlocking.is_route_set(route_1, "IC1234") == IsRouteSetResult.ROUTE_SET_FOR_WRONG_TRAIN

    # Manipulate state of a point on the route
    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.point_controller.points["d43f9"].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.point_controller.points["d43f9"].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    # Manipulate state of the start signal
    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.signal_controller.signals["0ab8c048-f4ea-4d4d-97cd-510d0b05651f"].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.signal_controller.signals["0ab8c048-f4ea-4d4d-97cd-510d0b05651f"].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    # Manipulate state of a segment
    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.track_controller.tracks["94742"].segments[0].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.track_controller.tracks["94742"].segments[0].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

def test_reset_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "go", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)

    asyncio.run(interlocking.reset_route(route_1, "RB101"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "RB101", "halt", OccupancyState.FREE)
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.FREE)


def test_not_allow_route_twice():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, False, "RB102"))


def test_not_allow_conflicting_routes():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, False, "RB102"))


def test_route_conflicts():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_es1_as1 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    route_es1_as2 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS2")
    route_es2_as3 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")
    route_es2_as4 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS4")
    route_bs4_es2 = topologyhelper.get_route_by_signal_names(topology, "60BS4", "60ES2")
    route_bs4_bs5 = topologyhelper.get_route_by_signal_names(topology, "60BS4", "60BS5")
    route_bs5_bs6 = topologyhelper.get_route_by_signal_names(topology, "60BS5", "60BS6")
    route_bs6_bs7 = topologyhelper.get_route_by_signal_names(topology, "60BS6", "60BS7")
    route_bs1_bs2 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    route_bs2_bs3 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")

    assert not interlocking.do_two_routes_collide(route_es1_as1, route_bs6_bs7)
    assert interlocking.do_two_routes_collide(route_es1_as2, route_es1_as1)
    assert interlocking.do_two_routes_collide(route_es2_as3, route_es2_as3)
    assert interlocking.do_two_routes_collide(route_es2_as4, route_es1_as2)
    assert interlocking.do_two_routes_collide(route_bs4_es2, route_bs4_es2)
    assert not interlocking.do_two_routes_collide(route_bs4_es2, route_bs1_bs2)
    assert interlocking.do_two_routes_collide(route_bs4_bs5, route_bs2_bs3)
    assert interlocking.do_two_routes_collide(route_bs5_bs6, route_bs4_bs5)
    assert interlocking.do_two_routes_collide(route_bs6_bs7, route_bs5_bs6)
    assert not interlocking.do_two_routes_collide(route_bs1_bs2, route_bs4_es2)
    assert not interlocking.do_two_routes_collide(route_bs2_bs3, route_es2_as4)
    assert not interlocking.do_two_routes_collide(route_es1_as1, route_bs4_es2)
    assert interlocking.do_two_routes_collide(route_es1_as2, route_es2_as3)
    assert interlocking.do_two_routes_collide(route_es2_as3, route_bs4_es2)
    assert not interlocking.do_two_routes_collide(route_es2_as4, route_bs4_bs5)


def test_missing_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    edge: YaramoEdge = YaramoEdge(YaramoNode(), YaramoNode())
    start_signal: YaramoSignal = YaramoSignal(direction="in",
                                              distance_edge=0.0,
                                              function="Einfahr_Signal",
                                              kind="Hauptsignal",
                                              edge=edge)
    route: YaramoRoute = YaramoRoute(start_signal=start_signal)
    assert interlocking.get_route_from_yaramo_route(route) is None


def test_failing_point():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    signal_tr = range(0, 1)
    point_tr = range(0, 1)
    rwip = RandomWaitInfrastructureProvider(fail_probability=0.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr,
                                            always_fail_for=["d43f9"])
    interlocking = interlockinghelper.get_interlocking(topology, infrastructure_provider=[rwip])
    route_bs1_bs2 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs1_bs2, False, "RB101"))
    route_bs2_bs3 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs2_bs3, True, "RB101"))


def test_failing_signal():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    signal_tr = range(0, 1)
    point_tr = range(0, 1)
    rwip = RandomWaitInfrastructureProvider(fail_probability=0.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr,
                                            always_fail_for=["60BS1"])
    interlocking = interlockinghelper.get_interlocking(topology, infrastructure_provider=[rwip])
    route_bs1_bs2 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs1_bs2, False, "RB101"))
    route_bs2_bs3 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs2_bs3, True, "RB101"))


def test_consecutive_routes():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    # Consecutive routes, everything fine.
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB101"))

    asyncio.run(interlocking.reset())

    # Totally different routes, not allowed
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, False, "RB101"))

    asyncio.run(interlocking.reset())

    # Reduce speed to avoid overlap
    for route in interlocking.routes:
        route.yaramo_route.maximum_speed = 30

    # Overlapping routes without overlap, not allowed
    # (caused issue https://github.com/simulate-digital-rail/interlocking/issues/14)
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60BS6", "60BS7")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, False, "RB101"))

    asyncio.run(interlocking.reset())

    # Test three in a row consecutive routes, everything fine
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60ES1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB101"))
    route_3 = topologyhelper.get_route_by_signal_names(topology, "60AS1", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_3, True, "RB101"))

    asyncio.run(interlocking.reset())

    # Increase speed to add overlap
    for route in interlocking.routes:
        route.yaramo_route.maximum_speed = 50

    # Test three in a row consecutive routes, everything fine
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60ES1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB101"))
    route_3 = topologyhelper.get_route_by_signal_names(topology, "60AS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_3, True, "RB101"))


class TestConsecutiveRouteDetectionWithTwoLastTracks(unittest.TestCase):

    def test_consecutive_route_detection_with_two_last_tracks(self):
        topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
        interlocking = interlockinghelper.get_interlocking(topology)

        route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
        route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
        route_3 = topologyhelper.get_route_by_signal_names(topology, "60AS1", "60BS3")

        ixl_route_1 = interlocking.get_route_from_yaramo_route(route_1)
        ixl_route_2 = interlocking.get_route_from_yaramo_route(route_2)

        ixl_route_1.used_by = "RB101"
        ixl_route_2.used_by = "RB101"
        interlocking.active_routes.append(ixl_route_1)
        interlocking.active_routes.append(ixl_route_2)

        with self.assertRaises(ValueError) as error:
            asyncio.run(interlocking.set_route(route_3, "RB101"))

        self.assertEqual(str(error.exception), "Multiple last routes found")


class TestFreeRouteExceptions(unittest.TestCase):

    def test_free_route_without_setting_route_before(self):
        topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
        interlocking = interlockinghelper.get_interlocking(topology)

        some_route: YaramoRoute = list(topology.routes.values())[0]
        with self.assertRaises(Exception) as exception:
            interlocking.free_route(some_route, "RB101")

        self.assertEqual(str(exception.exception), f"Route from {some_route.start_signal.name} to "
                                                   f"{some_route.end_signal.name} was not set.")

    def test_free_route_with_wrong_train_id(self):
        topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
        interlocking = interlockinghelper.get_interlocking(topology)

        some_route: YaramoRoute = list(topology.routes.values())[0]
        correct_train_id = "RB101"
        other_train_id = "OtherTrainID102"
        asyncio.run(interlockinghelper.set_route(interlocking, some_route, True, correct_train_id))

        with self.assertRaises(Exception) as exception:
            interlocking.free_route(some_route, other_train_id)

        self.assertEqual(str(exception.exception), f"Wrong Train ID: The route from {some_route.start_signal.name} to "
                                                   f"{some_route.end_signal.name} was not set with the train id "
                                                   f"{other_train_id}.")


class TestResetRouteExceptions(unittest.TestCase):

    def test_reset_route_without_setting_route_before(self):
        topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
        interlocking = interlockinghelper.get_interlocking(topology)

        some_route: YaramoRoute = list(topology.routes.values())[0]
        with self.assertRaises(Exception) as exception:
            asyncio.run(interlocking.reset_route(some_route, "RB101"))

        self.assertEqual(str(exception.exception), f"Route from {some_route.start_signal.name} to "
                                                   f"{some_route.end_signal.name} was not set.")

    def test_reset_route_with_wrong_train_id(self):
        topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
        interlocking = interlockinghelper.get_interlocking(topology)

        some_route: YaramoRoute = list(topology.routes.values())[0]
        correct_train_id = "RB101"
        other_train_id = "OtherTrainID102"
        asyncio.run(interlockinghelper.set_route(interlocking, some_route, True, correct_train_id))

        with self.assertRaises(Exception) as exception:
            asyncio.run(interlocking.reset_route(some_route, other_train_id))

        self.assertEqual(str(exception.exception), f"Wrong Train ID: The route from {some_route.start_signal.name} to "
                                                   f"{some_route.end_signal.name} was not set with the train id "
                                                   f"{other_train_id}.")


# if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # test_driving()
