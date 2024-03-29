import asyncio
import logging
from interlocking.model import Signal


class SignalController(object):

    def __init__(self, infrastructure_providers):
        self.signals: dict[str, Signal] = {}
        self.infrastructure_providers = infrastructure_providers

    async def reset(self):
        # Run non-concurrently
        for signal_id in self.signals:
            await self.set_signal_halt(self.signals[signal_id])

    async def set_route(self, route):
        return await self.set_signal_go(route.start_signal)

    async def set_signal_halt(self, signal):
        return await self.set_signal_state(signal, "halt")

    async def set_signal_go(self, signal):
        return await self.set_signal_state(signal, "go")

    async def set_signal_state(self, signal, state):
        if signal.state == state:
            # Everything is fine
            return True
        logging.info(f"--- Set signal {signal.yaramo_signal.name} to {state}")

        results = []
        for infrastructure_provider in self.infrastructure_providers:
            results.append(await infrastructure_provider.call_set_signal_state(signal.yaramo_signal, state))

        # tasks = []
        # async with asyncio.TaskGroup() as tg:
        #    for infrastructure_provider in self.infrastructure_providers:
        #        tasks.append(tg.create_task(infrastructure_provider.call_set_signal_state(signal.yaramo_signal, state)))
        # if all(list(map(lambda task: task.result(), tasks))):
        if all(results):
            signal.state = state
            return True
        else:
            # TODO: Incident
            return False

    async def reset_route(self, route):
        await self.set_signal_halt(route.start_signal)

    def print_state(self):
        logging.debug("State of Signals:")
        for signal_uuid in self.signals:
            signal = self.signals[signal_uuid]
            logging.debug(f"{signal.yaramo_signal.name}: {signal.state}")
