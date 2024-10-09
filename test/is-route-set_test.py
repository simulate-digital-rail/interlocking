from .helper import topologyhelper, interlockinghelper
from interlocking.model import OccupancyState
from interlocking.model.helper import IsRouteSetResult
import asyncio


def _get_interlocking_topology_and_routes():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)
    route_1 = topologyhelper.get_route_by_signal_names(topology, "60BS1", "60BS2")
    route_2 = topologyhelper.get_route_by_signal_names(topology, "60ES2", "60AS3")
    return interlocking, topology, route_1, route_2


def test_is_route_set():
    interlocking, topology, route_1, route_2 = _get_interlocking_topology_and_routes()
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))

    # Route set with correct train
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_SET_CORRECTLY
    # Route not set
    assert interlocking.is_route_set(route_2, "RB101") == IsRouteSetResult.ROUTE_NOT_SET
    # Route set with wrong train
    assert interlocking.is_route_set(route_1, "IC1234") == IsRouteSetResult.ROUTE_SET_FOR_WRONG_TRAIN


def test_point_state_manipulation():
    interlocking, topology, route_1, route_2 = _get_interlocking_topology_and_routes()
    point_id = "d43f9"

    # Manipulate state of a point on the route
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.point_controller.points[point_id].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.point_controller.points[point_id].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY


def test_signal_state_manipulation():
    interlocking, topology, route_1, route_2 = _get_interlocking_topology_and_routes()
    signal_uuid = "0ab8c048-f4ea-4d4d-97cd-510d0b05651f"

    # Manipulate state of the start signal
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.signal_controller.signals[signal_uuid].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.signal_controller.signals[signal_uuid].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY


def test_segment_state_manipulation():
    interlocking, topology, route_1, route_2 = _get_interlocking_topology_and_routes()
    track_id = "94742"

    # Manipulate state of a segment
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.track_controller.tracks[track_id].segments[0].state = OccupancyState.FREE
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY

    asyncio.run(interlocking.reset())
    asyncio.run(interlockinghelper.set_route(interlocking, route_1, True, "RB101"))
    interlocking.track_controller.tracks[track_id].segments[0].used_by = set()
    assert interlocking.is_route_set(route_1, "RB101") == IsRouteSetResult.ROUTE_NOT_SET_CORRECTLY


