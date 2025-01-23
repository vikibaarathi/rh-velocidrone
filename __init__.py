from eventmanager import Evt
from .velo import Velo

def initialize(rhapi):
    velo = Velo(rhapi)
    rhapi.events.on(Evt.STARTUP, velo.startsocket)
    rhapi.events.on(Evt.RACE_START, velo.startrace)



