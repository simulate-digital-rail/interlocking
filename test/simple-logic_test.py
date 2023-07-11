from .helper import topologyhelper, interlockinghelper
from interlocking.model import OccupancyState
import asyncio


def test_simple_logic_test():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology)

    route = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route, True, "RB101"))

    # point on the route between 60BS2 and 60BS3
    interlockinghelper.test_point(interlocking, "e641b", "RB101", "right", OccupancyState.RESERVED)


# if __name__ == "__main__":
    # test_simple_logic_test()
