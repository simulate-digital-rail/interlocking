from .infrastructureprovider import InfrastructureProvider
import time
import logging


class LoggingInfrastructureProvider(InfrastructureProvider):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def set_signal_aspect(self, yaramo_signal, target_aspect):
        logging.info(f"{time.strftime('%X')} Set signal {yaramo_signal.name} to {target_aspect}")
        return True

    async def turn_point(self, yaramo_point, target_orientation: str):
        point_id = yaramo_point.uuid[-5:]
        logging.info(f"{time.strftime('%X')} Turn point {point_id} to {target_orientation}")
        return True
