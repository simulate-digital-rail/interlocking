from .infrastructureprovider import InfrastructureProvider
import time
import logging
import random
import asyncio


class RandomWaitInfrastructureProvider(InfrastructureProvider):

    def __init__(self, allow_fail):
        super().__init__()
        self.allow_fail = allow_fail

    async def set_signal_state(self, yaramo_signal, target_state):
        # Time to set signal according to
        # https://www.graefelfing.de/fileadmin/user_upload/Ortsplanung_Mobilitaet/Verkehrsplanung/Verkehrsuntersuchungen/Bahnuebergang_Brunhamstrasse/Gutachten-Schliesszeiten-Bericht.pdf
        wait = random.randint(2, 4)
        signal_id = yaramo_signal.uuid[-5:]
        await asyncio.sleep(wait)
        if random.randint(0, 3) > 0 or not self.allow_fail:
            logging.info(f"{time.strftime('%X')} Completed setting signal {signal_id} to {target_state} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed setting signal {signal_id} to {target_state} (waited {wait})")
        return False

    async def turn_point(self, yaramo_point: str, target_orientation: str):
        # Time to turn point according to
        # https://de.wikipedia.org/wiki/Weiche_(Bahn)#Umlaufzeiten
        wait = random.randint(5, 7)
        point_id = yaramo_point.uuid[-5:]
        await asyncio.sleep(wait)
        if random.randint(0, 3) > 0 or not self.allow_fail:
            logging.info(f"{time.strftime('%X')} Completed turning point {point_id} to {target_orientation} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed turning point {point_id} to {target_orientation} (waited {wait})")
        return False
