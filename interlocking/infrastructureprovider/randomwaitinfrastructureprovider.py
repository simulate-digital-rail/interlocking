from .infrastructureprovider import InfrastructureProvider
import time
import logging
import random
import asyncio


class RandomWaitInfrastructureProvider(InfrastructureProvider):

    # Time to set signal according to
    # https://www.graefelfing.de/fileadmin/user_upload/Ortsplanung_Mobilitaet/Verkehrsplanung/Verkehrsuntersuchungen/Bahnuebergang_Brunhamstrasse/Gutachten-Schliesszeiten-Bericht.pdf
    # Time to turn point according to
    # https://de.wikipedia.org/wiki/Weiche_(Bahn)#Umlaufzeiten

    def __init__(self, allow_fail, signal_time_range=range(2, 5), point_turn_time_range=range(5, 8)):
        super().__init__()
        self.allow_fail = allow_fail
        self.signal_time_range = signal_time_range
        self.point_turn_time_range = point_turn_time_range

    async def set_signal_aspect(self, yaramo_signal, target_aspect):
        wait = random.sample(self.signal_time_range, 1)[0]
        await asyncio.sleep(wait)
        if random.randint(0, 3) > 0 or not self.allow_fail:
            logging.info(f"{time.strftime('%X')} Completed setting signal {yaramo_signal.name} to {target_aspect} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed setting signal {yaramo_signal.name} to {target_aspect} (waited {wait})")
        return False

    async def turn_point(self, yaramo_point, target_orientation: str):
        wait = random.sample(self.point_turn_time_range, 1)[0]
        point_id = yaramo_point.uuid[-5:]
        await asyncio.sleep(wait)
        if random.randint(0, 3) > 0 or not self.allow_fail:
            logging.info(f"{time.strftime('%X')} Completed turning point {point_id} to {target_orientation} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed turning point {point_id} to {target_orientation} (waited {wait})")
        return False
