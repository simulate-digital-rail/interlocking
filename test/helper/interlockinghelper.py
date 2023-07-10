from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import InfrastructureProvider, LoggingInfrastructureProvider
from yaramo.model import Route, Topology
from interlocking.model import OccupancyState


def get_interlocking(topology: Topology, infrastructure_provider: list[InfrastructureProvider] = None):
    if infrastructure_provider is None:
        infrastructure_provider = []
    infrastructure_provider.append(LoggingInfrastructureProvider())
    interlocking = Interlocking(infrastructure_provider)
    interlocking.prepare(topology)
    return interlocking


async def set_route(interlocking: Interlocking, route: Route, should_be_able_to_set: bool, train_id: str):
    set_route_result = await interlocking.set_route(route, train_id)
    assert set_route_result.success == should_be_able_to_set
    return set_route_result


def test_point(interlocking: Interlocking, point_id: str, train_id: str, orientation: str, state: OccupancyState):
    point = interlocking.point_controller.points[point_id]
    assert train_id in point.used_by
    assert point.orientation == orientation
    assert point.state == state
