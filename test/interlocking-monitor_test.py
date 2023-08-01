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

    some_route = list(topology.routes.values())[0]
    assert not ilm.route_results[some_route.uuid].was_set
    assert not ilm.route_results[some_route.uuid].was_freed
    assert ilm.route_results[some_route.uuid].get_coverage() == 0.0

    asyncio.run(interlocking.set_route(some_route, "RB101"))
    assert ilm.route_results[some_route.uuid].was_set
    assert ilm.route_results[some_route.uuid].get_coverage() == 1/3
    interlocking.free_route(some_route, "RB101")
    assert ilm.route_results[some_route.uuid].was_freed
    assert ilm.route_results[some_route.uuid].get_coverage() == 2/3


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
