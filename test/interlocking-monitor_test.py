from .helper import topologyhelper
from interlockinglogicmonitor import InterlockingLogicMonitor
from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import LoggingInfrastructureProvider
import asyncio


def test_set_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    ilm = InterlockingLogicMonitor(topology)
    interlocking = Interlocking(LoggingInfrastructureProvider(), interlocking_logic_monitor=ilm)
    interlocking.prepare(topology)

    some_route = list(topology.routes.values())[0]
    assert not ilm.route_results[some_route.uuid].was_set
    assert ilm.route_results[some_route.uuid].get_coverage() == 0.0
    asyncio.run(interlocking.set_route(some_route, "RB101"))
    assert ilm.route_results[some_route.uuid].was_set
    assert ilm.route_results[some_route.uuid].get_coverage() == 1/3


def test_free_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    ilm = InterlockingLogicMonitor(topology)
    interlocking = Interlocking(LoggingInfrastructureProvider(), interlocking_logic_monitor=ilm)
    interlocking.prepare(topology)

    route_bs5_bs6 = topologyhelper.get_route_by_signal_names(topology, "60BS5", "60BS6")
    assert not ilm.route_results[route_bs5_bs6.uuid].was_set
    assert not ilm.route_results[route_bs5_bs6.uuid].was_freed
    assert ilm.route_results[route_bs5_bs6.uuid].get_coverage() == 0.0

    asyncio.run(interlocking.set_route(route_bs5_bs6, "RB101"))
    assert ilm.route_results[route_bs5_bs6.uuid].was_set
    assert ilm.route_results[route_bs5_bs6.uuid].get_coverage() == 1/3

    # Drive Route
    ip = interlocking.infrastructure_providers[0]
    asyncio.run(ip.tds_count_in("b8e69-2", "RB101"))
    asyncio.run(ip.tds_count_out("b8e69-2", "RB101"))

    interlocking.free_route(route_bs5_bs6, "RB101")
    assert ilm.route_results[route_bs5_bs6.uuid].was_freed
    assert ilm.route_results[route_bs5_bs6.uuid].get_coverage() == 2/3


def test_reset_route():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    ilm = InterlockingLogicMonitor(topology)
    interlocking = Interlocking(LoggingInfrastructureProvider(), interlocking_logic_monitor=ilm)
    interlocking.prepare(topology)

    some_route = list(topology.routes.values())[0]
    assert not ilm.route_results[some_route.uuid].was_set
    assert not ilm.route_results[some_route.uuid].was_reset
    assert ilm.route_results[some_route.uuid].get_coverage() == 0.0

    asyncio.run(interlocking.set_route(some_route, "RB101"))
    assert ilm.route_results[some_route.uuid].was_set
    assert ilm.route_results[some_route.uuid].get_coverage() == 1/3
    asyncio.run(interlocking.reset_route(some_route, "RB101"))
    assert ilm.route_results[some_route.uuid].was_reset
    assert ilm.route_results[some_route.uuid].get_coverage() == 2/3
