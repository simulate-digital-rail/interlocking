from .helper import topologyhelper, interlockinghelper
from interlocking.model import OccupancyState
from interlocking.infrastructureprovider import RandomWaitInfrastructureProvider
from yaramo.model import Route as YaramoRoute, Signal as YaramoSignal, Edge as YaramoEdge, Node as YaramoNode
import asyncio


def test_reset():
    print("test")
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB102"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "go")
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)

    interlockinghelper.test_track(interlocking, "3a70a-0", "RB102", OccupancyState.RESERVED)
    interlockinghelper.test_signal(interlocking, "60ES2", "go")
    interlockinghelper.test_point(interlocking, "fd73d", "RB102", "right", OccupancyState.RESERVED)

    asyncio.run(interlocking.reset())

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "halt")
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "undefined", OccupancyState.FREE)

    interlockinghelper.test_track(interlocking, "3a70a-0", "RB102", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60ES2", "halt")
    interlockinghelper.test_point(interlocking, "fd73d", "RB102", "undefined", OccupancyState.FREE)


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
    interlockinghelper.test_signal(interlocking, "60BS1", "go")

    route_2 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_2, True, "RB101"))

    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "fb749", "RB101", "right", OccupancyState.RESERVED)
    interlockinghelper.test_point(interlocking, "e641b", "RB101", "right", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)

    # "Drive" some train
    ip = interlocking.infrastructure_providers[0]
    asyncio.run(ip.tds_count_in("de139-1", "RB101"))
    interlockinghelper.test_signal(interlocking, "60BS1", "halt")
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


def test_reset_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.RESERVED_OVERLAP)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "go")
    interlockinghelper.test_point(interlocking, "d43f9", "RB101", "left", OccupancyState.RESERVED)

    asyncio.run(interlocking.reset_route(route_1, "RB101"))

    interlockinghelper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "b8e69-3", "RB101", OccupancyState.FREE)
    interlockinghelper.test_track(interlocking, "a8f44-0", "RB101", OccupancyState.FREE)
    interlockinghelper.test_signal(interlocking, "60BS1", "halt")
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

# if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # test_driving()
