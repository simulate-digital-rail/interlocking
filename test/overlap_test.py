import helper
from interlocking.model import OccupancyState, Route, Overlap
import asyncio


def test_simple_overlap():
    topology = helper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = helper.get_interlocking(topology)
    route_bs4_bs5 = helper.get_route_by_signal_names(topology, "60BS4", "60BS5")
    interlocking_route: Route = interlocking.get_route_from_yaramo_route(route_bs4_bs5)
    overlaps: list[Overlap] = interlocking_route.get_overlaps_of_route()
    assert len(overlaps) == 1
    overlap = overlaps[0]
    assert overlap.is_full()
    assert len(overlap.segments) == 3
    segment_ids: set[str] = set(map(lambda seg: seg.segment_id, overlap.segments))
    assert "b8e69-2" in segment_ids
    assert "b8e69-1" in segment_ids
    assert "b8e69-0" in segment_ids
    assert "94742-0" not in segment_ids


def test_multiple_overlaps():
    topology = helper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = helper.get_interlocking(topology)
    route_bs4_es2 = helper.get_route_by_signal_names(topology, "60BS4", "60ES2")
    interlocking_route: Route = interlocking.get_route_from_yaramo_route(route_bs4_es2)
    overlaps: list[Overlap] = interlocking_route.get_overlaps_of_route()
    assert len(overlaps) == 2


def test_overlapping_overlaps():
    topology = helper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = helper.get_interlocking(topology)
    route_bs4_bs5 = helper.get_route_by_signal_names(topology, "60BS4", "60BS5")
    route_bs5_bs6 = helper.get_route_by_signal_names(topology, "60BS5", "60BS6")

    # Setting both routes should be possible
    helper.test_track(interlocking, "b8e69-2", "RB101", OccupancyState.FREE)
    helper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    asyncio.run(helper.set_route(interlocking, route_bs4_bs5, True, "RB101"))
    helper.test_track(interlocking, "b8e69-2", "RB101", OccupancyState.RESERVED_OVERLAP)
    helper.test_track(interlocking, "94742-0", "RB101", OccupancyState.FREE)
    asyncio.run(helper.set_route(interlocking, route_bs5_bs6, True, "RB101"))
    helper.test_track(interlocking, "b8e69-2", "RB101", OccupancyState.RESERVED)
    helper.test_track(interlocking, "94742-0", "RB101", OccupancyState.RESERVED_OVERLAP)