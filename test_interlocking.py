
from interlocking import Interlocking
from metadatacontroller import MetadataController

def test_01():

    metadata_controller = MetadataController()
    metadata_controller.load_metadata('data/Lausitz-LEAG.metadata.json ')

    def move_point_callback(point_id,orientation):
        print(f"Move Point {point_id} {orientation}")

    
    def set_signal_state_callback(signal_id,state,wirkrichtung):
        print(f"Set Signal {signal_id} {state} {wirkrichtung} ")

    interlocking = Interlocking('data/Lausitz-LEAG',move_point_callback,set_signal_state_callback)
    interlocking.stations = metadata_controller.stations

    interlocking.prepare([])

    #for route in interlocking.routes:
    #    print(route)
    #    interlocking.set_route(route,"train")

    print("Found Routes:")
    for route in interlocking.routes:
        print(f"{route.to_string()}\t(ID: {route.id}; Available in SUMO: {route.available_in_sumo}; UUID: {route.route_uuid})")


    #traindetection
    #interlocking.train_detection_controller.count_in("roadid")

    #interlocking.print_state()

   

