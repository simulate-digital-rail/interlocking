from planpro_importer.reader import PlanProReader
from railwayroutegenerator.routegenerator import RouteGenerator
from interlocking.interlockinginterface import Interlocking
from interlocking.infrastructureprovider import LoggingInfrastructureProvider, RandomWaitInfrastructureProvider
from interlocking.model.helper import Settings
from interlockinglogicmonitor import MonitorInfrastructureProvider, InterlockingLogicMonitor, Evaluation, CoverageCriteria
import asyncio
import logging


async def test_01():

    path = __file__.split("test_interlocking.py")[0]
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

    infrastructure_provider = [LoggingInfrastructureProvider(),
                               #RandomWaitInfrastructureProvider(allow_fail=False),
                               MonitorInfrastructureProvider(topology)]

    monitor = InterlockingLogicMonitor(topology)
    interlocking = Interlocking(infrastructure_provider, Settings(max_number_of_points_at_same_time=3), monitor)
    interlocking.prepare(topology)
    interlocking.print_state()

    async def set_route(_start_signal_name, _end_signal_name, _should_be_able_to_set, _train_id):
        for _route_uuid in topology.routes:
            _route = topology.routes[_route_uuid]
            if _route.start_signal.name == _start_signal_name and _route.end_signal.name == _end_signal_name:
                logging.debug(f"### Set Route {_start_signal_name} -> {_end_signal_name}")
                _set_route_result = await interlocking.set_route(_route, _train_id)
                assert (_set_route_result.success == _should_be_able_to_set)
                interlocking.print_state()
                return _set_route_result

    def free_route(_start_signal_name, _end_signal_name, _train_id):
        for _route_uuid in topology.routes:
            _route = topology.routes[_route_uuid]
            if _route.start_signal.name == _start_signal_name and _route.end_signal.name == _end_signal_name:
                logging.debug(f"### Free Route {_start_signal_name} -> {_end_signal_name}")
                interlocking.free_route(_route, _train_id)
                # interlocking.print_state()

    async def reset_route(_start_signal_name, _end_signal_name, _train_id):
        for _route_uuid in topology.routes:
            _route = topology.routes[_route_uuid]
            if _route.start_signal.name == _start_signal_name and _route.end_signal.name == _end_signal_name:
                logging.debug(f"### Reset Route {_start_signal_name} -> {_end_signal_name}")
                await interlocking.reset_route(_route, _train_id)
                # interlocking.print_state()

    async def drive_some_route_backwards():
        set_route_result = await set_route("60BS1", "60BS2", True, "RB101")
        interlocking.print_state()
        logging.info(f"Set route success: {set_route_result.success}, "
                     f"Route Formation Time: {set_route_result.route_formation_time}")
        if set_route_result.success:
            # "Drive" some train
            print("Driving!")
            await infrastructure_provider[0].tds_count_in("b8e69-1", "RB101")
            await infrastructure_provider[0].tds_count_in("b8e69-0", "RB101")
            await infrastructure_provider[0].tds_count_out("b8e69-1", "RB101")
            await infrastructure_provider[0].tds_count_in("94742-0", "RB101")
            await infrastructure_provider[0].tds_count_out("b8e69-0", "RB101")
            await infrastructure_provider[0].tds_count_in("de139-2", "RB101")
            await infrastructure_provider[0].tds_count_out("94742-0", "RB101")
            await infrastructure_provider[0].tds_count_out("de139-2", "RB101")
            free_route("60BS6", "60BS7", "RB101")
            interlocking.print_state()

    async def drive_some_route_forwards():
        set_first_route_result = await set_route("60BS1", "60BS2", True, "RB101")
        interlocking.print_state()
        logging.info(f"Set route success: {set_first_route_result.success}, "
                     f"Route Formation Time: {set_first_route_result.route_formation_time}")
        if set_first_route_result.success:
            set_second_route_result = await set_route("60BS2", "60BS3", True, "RB101")
            interlocking.print_state()
            logging.info(f"Set route success: {set_second_route_result.success}, "
                         f"Route Formation Time: {set_second_route_result.route_formation_time}")
            if set_second_route_result.success:
                # "Drive" some train
                print("Driving!")
                await infrastructure_provider[0].tds_count_in("de139-1", "RB101")
                await infrastructure_provider[0].tds_count_in("de139-2", "RB101")
                await infrastructure_provider[0].tds_count_out("de139-1", "RB101")
                await infrastructure_provider[0].tds_count_in("94742-0", "RB101")
                await infrastructure_provider[0].tds_count_out("de139-2", "RB101")
                await infrastructure_provider[0].tds_count_in("b8e69-0", "RB101")
                await infrastructure_provider[0].tds_count_out("94742-0", "RB101")
                await infrastructure_provider[0].tds_count_in("b8e69-1", "RB101")
                await infrastructure_provider[0].tds_count_out("b8e69-0", "RB101")
                free_route("60BS1", "60BS2", "RB101")
                interlocking.print_state()
                await infrastructure_provider[0].tds_count_in("b8e69-2", "RB101")
                await infrastructure_provider[0].tds_count_out("b8e69-1", "RB101")
                await infrastructure_provider[0].tds_count_in("b8e69-3", "RB101")
                await infrastructure_provider[0].tds_count_out("b8e69-2", "RB101")
                await infrastructure_provider[0].tds_count_in("a8f44-0", "RB101")
                await infrastructure_provider[0].tds_count_out("b8e69-3", "RB101")
                await infrastructure_provider[0].tds_count_out("a8f44-0", "RB101")
                interlocking.print_state()
                free_route("60BS2", "60BS3", "RB101")
                interlocking.print_state()

    await drive_some_route_forwards()
    evaluation = Evaluation(monitor, infrastructure_provider[-1])
    logging.info(f"Coverage: {evaluation.get_coverage(CoverageCriteria.ALL)} "
                 f"{evaluation.get_coverage(CoverageCriteria.INFRASTRUCTURE_ONLY)} "
                 f"{evaluation.get_coverage(CoverageCriteria.ROUTES_ONLY)}")
    await interlocking.reset()

    await set_route("60ES2", "60AS4", True, "RB101")
    evaluation = Evaluation(monitor, infrastructure_provider[-1])
    evaluation.print_evaluation()
    await set_route("60ES2", "60AS3", False, "RB102")
    evaluation = Evaluation(monitor, infrastructure_provider[-1])
    evaluation.print_evaluation()
    await reset_route("60ES2", "60AS4", "RB101")
    await set_route("60ES2", "60AS3", True, "RB102")

    await interlocking.reset()
    evaluation = Evaluation(monitor, infrastructure_provider[-1])
    evaluation.print_evaluation()

    # Get conflicts:
    for route_uuid_1 in topology.routes:
        for route_uuid_2 in topology.routes:
            if route_uuid_1 != route_uuid_2:
                route_1 = topology.routes[route_uuid_1]
                route_2 = topology.routes[route_uuid_2]
                do_collide = interlocking.do_two_routes_collide(route_1, route_2)
                logging.debug(f"{route_1.start_signal.name} -> {route_1.end_signal.name} and {route_2.start_signal.name} -> {route_2.end_signal.name}: collide? {do_collide}")

            
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_01())


   

