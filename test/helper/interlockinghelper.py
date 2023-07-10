from interlocking.interlockinginterface import Interlocking
from yaramo.model import Route


async def set_route(interlocking: Interlocking, route: Route, should_be_able_to_set: bool, train_id: str):
    set_route_result = await interlocking.set_route(route, train_id)
    assert set_route_result.success == should_be_able_to_set
    return set_route_result
