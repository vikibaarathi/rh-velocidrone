from eventmanager import Evt
from .velocidrone_controller import VeloController
from .velocidrone_import_controller import VeloImportController

def initialize(rhapi):
    velo = VeloController(rhapi)
    velo_importer = VeloImportController(rhapi)
    rhapi.events.on(Evt.STARTUP, velo.init_ui)
    rhapi.events.on(Evt.RACE_STAGE, velo.start_race_from_rh)
    rhapi.events.on(Evt.RACE_STOP, velo.stop_race_from_rh)
    rhapi.events.on(Evt.HEAT_SET, velo.set_current_heat)
    rhapi.events.on(Evt.DATA_IMPORT_INITIALIZE, velo_importer.init_importer)



