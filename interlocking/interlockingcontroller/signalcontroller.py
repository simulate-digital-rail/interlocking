import asyncio
import logging
from interlocking.model import OccupancyState, Signal


class SignalController(object):

    def __init__(self, infrastructure_providers):
        self.signals: dict[str, Signal] = {}
        self.infrastructure_providers = infrastructure_providers

    async def reset(self):
        # Run non-concurrently
        for signal_id in self.signals:
            await self.set_signal_halt(self.signals[signal_id])

    async def set_route(self, route, train_id: str):
        result = await self.set_signal_go(route.start_signal)
        if result:
            route.start_signal.state = OccupancyState.RESERVED
            route.start_signal.used_by.add(train_id)
        return result

    async def set_signal_halt(self, signal):
        return await self.set_signal_aspect(signal, "halt")

    async def set_signal_go(self, signal):
        return await self.set_signal_aspect(signal, "go")

    async def set_signal_aspect(self, signal, signal_aspect):
        if signal.signal_aspect == signal_aspect:
            # Everything is fine
            return True
        if signal.is_used_for_flank_protection is True:
            logging.error(f"Can not set signal aspect of signal {signal.yaramo_signal.name} to {signal_aspect}, "
                          f"since it is used for flank protection.")
            return False
        logging.info(f"--- Set signal {signal.yaramo_signal.name} to {signal_aspect}")

        results = []
        for infrastructure_provider in self.infrastructure_providers:
            results.append(await infrastructure_provider.call_set_signal_aspect(signal.yaramo_signal, signal_aspect))

        # tasks = []
        # async with asyncio.TaskGroup() as tg:
        #    for infrastructure_provider in self.infrastructure_providers:
        #        tasks.append(tg.create_task(infrastructure_provider.call_set_signal_aspect(signal.yaramo_signal, state)))
        # if all(list(map(lambda task: task.result(), tasks))):
        if all(results):
            signal.signal_aspect = signal_aspect
            return True
        else:
            # TODO: Incident
            return False

    def free_route(self, route, train_id: str):
        if route.start_signal.signal_aspect == "go":
            raise ValueError("Try to free route with start signal aspect is go")
        self.free_signal(route.start_signal, train_id)

    async def reset_route(self, route, train_id: str):
        result = await self.set_signal_halt(route.start_signal)
        if result:
            route.start_signal.state = OccupancyState.FREE
            if train_id in route.start_signal.used_by:
                route.start_signal.used_by.remove(train_id)

    def free_signal(self, signal: Signal, train_id: str):
        signal.state = OccupancyState.FREE
        signal.used_by.remove(train_id)

    def print_state(self):
        logging.debug("State of Signals:")
        for signal_uuid in self.signals:
            signal = self.signals[signal_uuid]
            logging.debug(f"{signal.yaramo_signal.name}: {signal.state} (Signal Aspect: {signal.signal_aspect}) "
                          f"(is used for FP: {signal.is_used_for_flank_protection})")
