from yaramo.model import Signal, Node
from interlocking.infrastructureprovider import InfrastructureProvider


class TrackOperationsInfrastructureProvider(InfrastructureProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.point_operations: set[tuple[Node, str]] = set()
        self.signal_operations: set[tuple[Signal, str]] = set()

    async def set_signal_aspect(self, yaramo_signal: Signal, target_aspect: str):
        await super().set_signal_aspect(yaramo_signal, target_aspect)
        self.signal_operations.add((yaramo_signal, target_aspect))
        return True

    async def turn_point(self, yaramo_point: Node, target_orientation: str):
        await super().turn_point(yaramo_point, target_orientation)
        self.point_operations.add((yaramo_point, target_orientation))
        return True

    def was_signal_set_to_aspect(self, yaramo_signal: Signal, aspect: str):
        for signal_operation in self.signal_operations:
            if signal_operation[0].name == yaramo_signal.name and signal_operation[1] == aspect:
                return True
        return False

    def was_point_turned_to(self, yaramo_point: Node, target_orientation: str):
        for point_operation in self.point_operations:
            if point_operation[0].uuid == yaramo_point.uuid and point_operation[1] == target_orientation:
                return True
        return False
