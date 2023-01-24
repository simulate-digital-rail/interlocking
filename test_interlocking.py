
from interlocking import Interlocking
from metadatacontroller import MetadataController

def test_01():

    metadata_controller = MetadataController()
    metadata_controller.load_metadata('data/Lausitz-LEAG.metadata.json ')


    interlocking = Interlocking(plan_pro_file_name='data/Lausitz-LEAG')
    interlocking.stations = metadata_controller.stations

    interlocking.prepare()
   

