from .infrastructureprovider import InfrastructureProvider
from yaramo.model import Signal, Node
import time
import logging
import random
import asyncio


class RandomWaitInfrastructureProvider(InfrastructureProvider):

    # Time to set signal according to
    # https://www.graefelfing.de/fileadmin/user_upload/Ortsplanung_Mobilitaet/Verkehrsplanung/Verkehrsuntersuchungen/Bahnuebergang_Brunhamstrasse/Gutachten-Schliesszeiten-Bericht.pdf
    # Time to turn point according to
    # https://de.wikipedia.org/wiki/Weiche_(Bahn)#Umlaufzeiten

    def __init__(self, fail_probability=0.0, signal_time_range: range = range(2, 5),
                 point_turn_time_range: range = range(5, 8), always_succeed_for: list[str] = None,
                 always_fail_for: list[str] = None, **kwargs):
        super().__init__(**kwargs)
        if always_succeed_for is None:
            always_succeed_for = []
        if always_fail_for is None:
            always_fail_for = []
        self.fail_probability = fail_probability
        self.signal_time_range = signal_time_range
        self.point_turn_time_range = point_turn_time_range
        self.always_succeed_for = always_succeed_for
        self.always_fail_for = always_fail_for

    async def set_signal_aspect(self, yaramo_signal: Signal, target_aspect: str):
        wait = random.sample(self.signal_time_range, 1)[0]
        await asyncio.sleep(wait)
        if (random.random() >= self.fail_probability or yaramo_signal.name in self.always_succeed_for) \
                and yaramo_signal.name not in self.always_fail_for:
            logging.info(f"{time.strftime('%X')} Completed setting signal {yaramo_signal.name} to {target_aspect} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed setting signal {yaramo_signal.name} to {target_aspect} (waited {wait})")
        return False

    async def turn_point(self, yaramo_point: Node, target_orientation: str):
        wait = random.sample(self.point_turn_time_range, 1)[0]
        point_id = yaramo_point.uuid[-5:]
        await asyncio.sleep(wait)
        if (random.random() >= self.fail_probability or point_id in self.always_succeed_for) \
                and point_id not in self.always_fail_for:
            logging.info(f"{time.strftime('%X')} Completed turning point {point_id} to {target_orientation} (waited {wait})")
            return True
        logging.warning(f"{time.strftime('%X')} Failed turning point {point_id} to {target_orientation} (waited {wait})")
        return False
