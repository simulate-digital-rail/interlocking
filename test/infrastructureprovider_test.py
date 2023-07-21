from .helper import topologyhelper, interlockinghelper, trackoperationsinfrastructureprovider
import asyncio
import unittest


class TestUsingBothLimiters(unittest.TestCase):

    def test_using_both_signal_limiters(self):
        with self.assertRaises(Exception) as exception:
            ip = trackoperationsinfrastructureprovider.TrackOperationsInfrastructureProvider(
                only_apply_for_signals=["99N1"],
                apply_for_all_signals_except=["99N2"]
            )

        self.assertEqual(str(exception.exception), f"You can not limit the infrastructure provider with "
                                                   f"only_apply_for_signals and apply_for_all_signals_except at "
                                                   f"the same time.")

    def test_using_both_point_limiters(self):
        with self.assertRaises(Exception) as exception:
            ip = trackoperationsinfrastructureprovider.TrackOperationsInfrastructureProvider(
                only_apply_for_points=["abcde"],
                apply_for_all_points_except=["abcde"]
            )

        self.assertEqual(str(exception.exception), f"You can not limit the infrastructure provider with "
                                                   f"only_apply_for_points and apply_for_all_points_except at "
                                                   f"the same time.")


def test_only_apply_for():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    ip = trackoperationsinfrastructureprovider.TrackOperationsInfrastructureProvider(only_apply_for_signals=["60ES1"],
                                                                                     only_apply_for_points=["fd73d"])
    interlocking = interlockinghelper.get_interlocking(topology, infrastructure_provider=[ip])
    route_es1_as1 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_es1_as1, True, "RB101"))
    route_bs2_bs3 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs2_bs3, True, "RB101"))

    signal_es1 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60ES1").yaramo_signal
    signal_bs2 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60BS2").yaramo_signal
    point_on_first_route = interlockinghelper.get_interlocking_point_by_id(interlocking, "fd73d").yaramo_node
    point_on_second_route = interlockinghelper.get_interlocking_point_by_id(interlocking, "e641b").yaramo_node
    assert ip.was_signal_set_to_aspect(signal_es1, "go")
    assert not ip.was_signal_set_to_aspect(signal_bs2, "go")
    assert ip.was_point_turned_to(point_on_first_route, "right")
    assert not ip.was_point_turned_to(point_on_second_route, "right")


def test_apply_for_all_except():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    ip = trackoperationsinfrastructureprovider.TrackOperationsInfrastructureProvider(
        apply_for_all_signals_except=["60ES1"],
        apply_for_all_points_except=["fd73d"]
    )
    interlocking = interlockinghelper.get_interlocking(topology, infrastructure_provider=[ip])
    route_es1_as1 = topologyhelper.get_route_by_signal_names(topology, "60ES1", "60AS1")
    asyncio.run(interlockinghelper.set_route(interlocking, route_es1_as1, True, "RB101"))
    route_bs2_bs3 = topologyhelper.get_route_by_signal_names(topology, "60BS2", "60BS3")
    asyncio.run(interlockinghelper.set_route(interlocking, route_bs2_bs3, True, "RB101"))

    signal_es1 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60ES1").yaramo_signal
    signal_bs2 = interlockinghelper.get_interlocking_signal_by_name(interlocking, "60BS2").yaramo_signal
    point_on_first_route_fd73d = interlockinghelper.get_interlocking_point_by_id(interlocking, "fd73d").yaramo_node
    point_on_first_route_fa9ea = interlockinghelper.get_interlocking_point_by_id(interlocking, "fa9ea").yaramo_node
    point_on_first_route_21b88 = interlockinghelper.get_interlocking_point_by_id(interlocking, "21b88").yaramo_node
    point_on_second_route = interlockinghelper.get_interlocking_point_by_id(interlocking, "e641b").yaramo_node
    assert not ip.was_signal_set_to_aspect(signal_es1, "go")
    assert ip.was_signal_set_to_aspect(signal_bs2, "go")
    assert not ip.was_point_turned_to(point_on_first_route_fd73d, "right")
    assert ip.was_point_turned_to(point_on_first_route_fa9ea, "left")
    assert ip.was_point_turned_to(point_on_first_route_21b88, "right")
    assert ip.was_point_turned_to(point_on_second_route, "right")