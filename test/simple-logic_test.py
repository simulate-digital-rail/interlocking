import helper
from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import LoggingInfrastructureProvider
from interlocking.model import OccupancyState
from interlocking.model.helper import Settings
import asyncio


def test_simple_logic_test():
    print("Run test")
    topology = helper.get_topology_from_planpro_file("./complex-example.ppxml")

    infrastructure_provider = [LoggingInfrastructureProvider()]

    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3))
    interlocking.prepare(topology)

    route = helper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(helper.set_route(interlocking, route, True, "RB101"))

    point_id = "e641b"  # point on the route between 60BS2 and 60BS3
    point = interlocking.point_controller.points[point_id]
    assert "RB101" in point.used_by
    assert point.orientation == "right"
    assert point.state == OccupancyState.RESERVED


print("TEst")
if __name__ == "__main__":
    test_simple_logic_test()
