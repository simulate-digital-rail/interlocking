from .helper import topologyhelper, interlockinghelper
from interlocking.infrastructureprovider import RandomWaitInfrastructureProvider
import asyncio


def test_fail_probability():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    signal_tr = range(0, 1)
    point_tr = range(0, 1)

    signal = topology.signals[list(topology.signals)[0]]
    point = topology.nodes[list(topology.nodes)[0]]

    # No random factor, always succeed
    rwip = RandomWaitInfrastructureProvider(fail_probability=0.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr)

    assert asyncio.run(rwip.turn_point(point, "left"))
    assert asyncio.run(rwip.turn_point(point, "left"))
    assert asyncio.run(rwip.turn_point(point, "left"))
    assert asyncio.run(rwip.turn_point(point, "left"))
    assert asyncio.run(rwip.turn_point(point, "left"))

    assert asyncio.run(rwip.set_signal_state(signal, "go"))
    assert asyncio.run(rwip.set_signal_state(signal, "go"))
    assert asyncio.run(rwip.set_signal_state(signal, "go"))
    assert asyncio.run(rwip.set_signal_state(signal, "go"))
    assert asyncio.run(rwip.set_signal_state(signal, "go"))

    # No random factor, always fail
    rwip = RandomWaitInfrastructureProvider(fail_probability=1.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr)

    assert not asyncio.run(rwip.turn_point(point, "left"))
    assert not asyncio.run(rwip.turn_point(point, "left"))
    assert not asyncio.run(rwip.turn_point(point, "left"))
    assert not asyncio.run(rwip.turn_point(point, "left"))
    assert not asyncio.run(rwip.turn_point(point, "left"))

    assert not asyncio.run(rwip.set_signal_state(signal, "go"))
    assert not asyncio.run(rwip.set_signal_state(signal, "go"))
    assert not asyncio.run(rwip.set_signal_state(signal, "go"))
    assert not asyncio.run(rwip.set_signal_state(signal, "go"))
    assert not asyncio.run(rwip.set_signal_state(signal, "go"))

    rwip = RandomWaitInfrastructureProvider(fail_probability=0.5, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr)
    success = 0
    fails = 0
    for i in range(0, 1000):
        if asyncio.run(rwip.turn_point(point, "left")):
            success = success + 1
        else:
            fails = fails + 1

    # Allow a bit of difference due to random factor
    assert 450 < success < 550
    assert 450 < fails < 550


def test_always_succeed_and_fail():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    signal_tr = range(0, 1)
    point_tr = range(0, 1)

    point_1 = topology.nodes[list(topology.nodes)[0]]
    point_2 = topology.nodes[list(topology.nodes)[1]]

    # Always succeed
    rwip = RandomWaitInfrastructureProvider(fail_probability=1.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr,
                                            always_succeed_for=[point_1.uuid[-5:]])
    assert asyncio.run(rwip.turn_point(point_1, "left"))
    assert not asyncio.run(rwip.turn_point(point_2, "left"))

    # Always fail
    rwip = RandomWaitInfrastructureProvider(fail_probability=0.0, signal_time_range=signal_tr,
                                            point_turn_time_range=point_tr,
                                            always_fail_for=[point_1.uuid[-5:]])
    assert not asyncio.run(rwip.turn_point(point_1, "left"))
    assert asyncio.run(rwip.turn_point(point_2, "left"))
