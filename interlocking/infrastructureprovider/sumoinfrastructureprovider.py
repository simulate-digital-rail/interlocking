from .infrastructureprovider import InfrastructureProvider
from yaramo.model import SignalDirection


class SUMOInfrastructureProvider(InfrastructureProvider):

    def __init__(self, traci_instance, **kwargs):
        super().__init__(**kwargs)
        self.traci_instance = traci_instance

    async def set_signal_state(self, yaramo_signal, target_state):
        if target_state == "go":
            self.traci_instance.trafficlight.setRedYellowGreenState(yaramo_signal.name, "GG")
        elif target_state == "halt":
            if yaramo_signal.direction == SignalDirection.IN:
                self.traci_instance.trafficlight.setRedYellowGreenState(yaramo_signal.name, "rG")
            else:
                self.traci_instance.trafficlight.setRedYellowGreenState(yaramo_signal.name, "Gr")
        return True

    async def turn_point(self, yaramo_point, target_orientation: str):
        # SUMO does not support the concept of points yet.
        return True
