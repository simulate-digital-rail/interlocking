from .infrastructureprovider import InfrastructureProvider
import time
import logging


class LoggingInfrastructureProvider(InfrastructureProvider):

    def __init__(self):
        super().__init__()

    async def set_signal_state(self, yaramo_signal, target_state):
        logging.info(f"{time.strftime('%X')} Set signal {yaramo_signal.name} to {target_state}")
        return True

    async def turn_point(self, yaramo_point, target_orientation: str):
        point_id = yaramo_point.uuid[-5:]
        logging.info(f"{time.strftime('%X')} Turn point {point_id} to {target_orientation}")
        return True
