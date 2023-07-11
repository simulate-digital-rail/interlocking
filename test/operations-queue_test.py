from .helper import topologyhelper, interlockinghelper
from interlocking.infrastructureprovider import InfrastructureProvider
from interlocking.model.helper import InterlockingOperation as ILXOP, InterlockingOperationType as ILXOPType
import asyncio


def test_operations_queue():
    asyncio.run(run_test())


async def run_test():
    topology = topologyhelper.get_topology_from_planpro_file("./complex-example.ppxml")
    interlocking = interlockinghelper.get_interlocking(topology, infrastructure_provider=[])

    async def fill_queue(_queue: asyncio.Queue, _ip: InfrastructureProvider):
        route_bs5_bs6 = topologyhelper.get_route_by_signal_names(topology, "60BS5", "60BS6")
        _queue.put_nowait(ILXOP(ILXOPType.SET_ROUTE, yaramo_route=route_bs5_bs6, train_id="RB101"))
        _queue.put_nowait(ILXOP(ILXOPType.PRINT_STATE))
        _queue.put_nowait(ILXOP(ILXOPType.RESET_ROUTE, yaramo_route=route_bs5_bs6, train_id="RB101"))
        _queue.put_nowait(ILXOP(ILXOPType.RESET))
        _queue.put_nowait(ILXOP(ILXOPType.SET_ROUTE, yaramo_route=route_bs5_bs6, train_id="RB101"))
        _queue.put_nowait(ILXOP(ILXOPType.TDS_COUNT_IN, segment_id="b8e69-2", train_id="RB101",
                                infrastructure_provider=_ip))
        _queue.put_nowait(ILXOP(ILXOPType.TDS_COUNT_OUT, segment_id="b8e69-2", train_id="RB101",
                                infrastructure_provider=_ip))
        _queue.put_nowait(ILXOP(ILXOPType.FREE_ROUTE, yaramo_route=route_bs5_bs6, train_id="RB101"))
        _queue.put_nowait(ILXOP(ILXOPType.EXIT))

    operations_queue = asyncio.Queue()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(interlocking.run_with_operations_queue(operations_queue))
        tg.create_task(fill_queue(operations_queue, interlocking.infrastructure_providers[0]))
