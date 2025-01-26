from eventmanager import Evt
from .velocidrone_controller import VeloController

def initialize(rhapi):
    velo = VeloController(rhapi)
    rhapi.events.on(Evt.STARTUP, velo.init_ui)



