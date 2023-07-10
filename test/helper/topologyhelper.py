from planpro_importer.reader import PlanProReader
from railwayroutegenerator.routegenerator import RouteGenerator
from yaramo.model import Topology


def get_topology_from_planpro_file(file_name: str):
    reader = PlanProReader(file_name)
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


def get_route_by_signal_names(topology: Topology, start_signal_name: str, end_signal_name: str):
    for route_uuid in topology.routes:
        route = topology.routes[route_uuid]
        if route.start_signal.name == start_signal_name and route.end_signal.name == end_signal_name:
            return route
