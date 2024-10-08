from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import InfrastructureProvider, LoggingInfrastructureProvider
from yaramo.model import Route, Topology
from interlocking.model import OccupancyState, TrackSegment, Track, Signal, Point


def get_interlocking(topology: Topology, infrastructure_provider: list[InfrastructureProvider] = None):
    if infrastructure_provider is None:
        interlocking = Interlocking(LoggingInfrastructureProvider())
    else:
        infrastructure_provider.append(LoggingInfrastructureProvider())
        interlocking = Interlocking(infrastructure_provider)
    interlocking.prepare(topology)
    return interlocking


async def set_route(interlocking: Interlocking, route: Route, should_be_able_to_set: bool, train_id: str):
    set_route_result = await interlocking.set_route(route, train_id)
    assert set_route_result.success == should_be_able_to_set
    return set_route_result


def free_route(interlocking: Interlocking, route: Route, train_id: str):
    interlocking.free_route(route, train_id)


def get_interlocking_signal_by_name(interlocking: Interlocking, signal_name: str):
    for signal_uuid in interlocking.signal_controller.signals:
        signal = interlocking.signal_controller.signals[signal_uuid]
        if signal.yaramo_signal.name == signal_name:
            return signal


def get_interlocking_point_by_id(interlocking: Interlocking, point_id: str):
    for _point_id in interlocking.point_controller.points:
        if _point_id == point_id:
            return interlocking.point_controller.points[point_id]

def get_interlocking_track_by_id(interlocking: Interlocking, segment_id: str):
    for track_id in interlocking.track_controller.tracks:
        track: Track = interlocking.track_controller.tracks[track_id]
        for _segment in track.segments:
            if _segment.segment_id == segment_id:
                return _segment
    return None


def test_point(interlocking: Interlocking, point_id: str, train_id: str, orientation: str, state: OccupancyState):
    point = interlocking.point_controller.points[point_id]
    assert point.state == state
    if state == OccupancyState.FREE:
        assert train_id not in point.used_by
    else:
        assert train_id in point.used_by
    assert point.orientation == orientation


def test_signal(interlocking: Interlocking, signal_id: str, train_id: str, signal_aspect: str, state: OccupancyState):
    signal: Signal or None = None
    for _signal in interlocking.signal_controller.signals.values():
        if _signal.yaramo_signal.name == signal_id:
            signal = _signal
    assert signal.state == state
    assert signal.signal_aspect == signal_aspect
    if state == OccupancyState.FREE:
        assert train_id not in signal.used_by
    else:
        assert train_id in signal.used_by


def test_track(interlocking: Interlocking, segment_id: str, train_id: str, state: OccupancyState):
    segment: TrackSegment | None = get_interlocking_track_by_id(interlocking, segment_id)
    assert segment is not None
    assert segment.state == state
    if state == OccupancyState.FREE:
        assert train_id not in segment.used_by
    else:
        assert train_id in segment.used_by
