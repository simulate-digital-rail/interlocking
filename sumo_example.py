from planpro_importer.reader import PlanProReader
from railwayroutegenerator.routegenerator import RouteGenerator
from sumoexporter import SUMOExporter
from interlocking.interlockinginterface import Interlocking
from interlocking.model.helper import Settings, InterlockingOperation, InterlockingOperationType
from interlocking.infrastructureprovider import LoggingInfrastructureProvider, SUMOInfrastructureProvider, RandomWaitInfrastructureProvider
import asyncio
import logging
import traci
from pathlib import Path


def prepare_yaramo_topology():
    path = __file__.split("sumo_example.py")[0]
    reader = PlanProReader(path + "/test/complex-example")
    topology = reader.read_topology_from_plan_pro_file()

    # TODO: At the moment, the railway route generator can not calculate max speeds since the edges have no max speeds
    outer_station_edges = ["88d820fc-95b4-408c-b418-a516877de139", "66adf559-7dd5-487f-bad7-8e256a8a8f44",
                           "f438d162-b5c4-4c0c-9d73-f55fad294742", "61d57b1b-2ae2-4637-897b-abbab41b8e69",
                           "f63e5398-f20c-47be-bbed-f7f8f8034bff"]
    for edge_uuid in topology.edges:
        edge = topology.edges[edge_uuid]
        if edge_uuid in outer_station_edges:
            edge.maximum_speed = 60
        else:
            edge.maximum_speed = 40

    generator = RouteGenerator(topology)
    generator.generate_routes()
    return topology


def get_route_by_signal_names(start_signal_name: str, end_signal_name: str, topology):
    for route_uuid in topology.routes:
        route = topology.routes[route_uuid]
        if route.start_signal.name == start_signal_name and route.end_signal.name == end_signal_name:
            return route
    return None


async def sumo_test():
    topology = prepare_yaramo_topology()

    traci.init(host="localhost", port=4444)

    infrastructure_provider = [LoggingInfrastructureProvider(),
                               RandomWaitInfrastructureProvider(allow_fail=False),
                               SUMOInfrastructureProvider(traci_instance=traci)]

    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3))
    interlocking.prepare(topology)
    interlocking.print_state()

    start_signal_name = "60AS3"
    end_signal_name = "60BS7"

    yaramo_route = get_route_by_signal_names(start_signal_name, end_signal_name, topology)
    await interlocking.set_route(yaramo_route, "RB101")
    traci.vehicle.add("Zug1", f"route_{start_signal_name}-{end_signal_name}", "regio")

    operations_queue = asyncio.Queue()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(interlocking.run_with_operations_queue(operations_queue))
        tg.create_task(run_simulation(operations_queue, infrastructure_provider))


async def run_simulation(op_queue, infrastructure_provider):
    sumo_ip = infrastructure_provider[2]
    traci.simulationStep()
    position = traci.vehicle.getRoadID("Zug1")
    if position.endswith("-re"):
        position = position[:-3]
    op_queue.put_nowait(InterlockingOperation(InterlockingOperationType.TDS_COUNT_IN,
                                              "RB101",
                                              infrastructure_provider=sumo_ip,
                                              segment_id=position))
    while len(traci.vehicle.getIDList()) > 0:
        traci.simulationStep()
        if len(traci.vehicle.getIDList()) == 0:
            break
        new_position = traci.vehicle.getRoadID("Zug1")
        if not new_position.startswith(":"):
            if new_position.endswith("-re"):
                new_position = new_position[:-3]
            if new_position != position:
                op_queue.put_nowait(InterlockingOperation(InterlockingOperationType.TDS_COUNT_OUT,
                                                          "RB101",
                                                          infrastructure_provider=sumo_ip,
                                                          segment_id=position))
                position = new_position
                op_queue.put_nowait(InterlockingOperation(InterlockingOperationType.TDS_COUNT_IN,
                                                          "RB101",
                                                          infrastructure_provider=sumo_ip,
                                                          segment_id=position))
        await asyncio.sleep(traci.simulation.getDeltaT())
    op_queue.put_nowait(InterlockingOperation(InterlockingOperationType.EXIT))


def create_sumo_scenario():
    topology = prepare_yaramo_topology()
    sumo_exporter = SUMOExporter(topology)
    sumo_exporter.convert()
    sumo_exporter.write_output()
    logging.info("Start sumo with:")
    logging.info("")
    logging.info("sumo-gui -c sumo-config/complex-example.scenario.sumocfg --remote-port 4444 --step-length=0.1 -S")
    logging.info("or")
    logging.info("sumo -c sumo-config/complex-example.scenario.sumocfg --remote-port 4444 --step-length=0.1")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if Path("./sumo-config/complex-example.scenario.sumocfg").is_file():
        asyncio.run(sumo_test())
    else:
        create_sumo_scenario()
