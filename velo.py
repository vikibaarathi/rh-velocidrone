import json
import requests
import logging
from sqlalchemy.ext.declarative import DeclarativeMeta
from RHUI import UIField, UIFieldType
from .datamanager import ClDataManager
from .velocidrone_client import VelocidroneClient
from RHUI import UIField, UIFieldType
import time
class Velo():

    heat_data = []

    def __init__(self,rhapi):
        # Pilot attributes
        velo_callsign = UIField(name = 'velo_callsign', label = 'Velocidrone Callsign', field_type = UIFieldType.TEXT)
        rhapi.fields.register_pilot_attribute(velo_callsign)
        self.logger = logging.getLogger(__name__)
        self._rhapi = rhapi
        self.client = VelocidroneClient()
        self._raceabort = False


    def create_pilot(self,pilot_data, pilot_name):
        return {
            "name": pilot_name,
            "holeshot": pilot_data["time"],
            "laps": [pilot_data["time"]],
            "lap": pilot_data["lap"],
            "finished": pilot_data["finished"]
        }
    def startsocket(self,args):
        print("Velocidrone plugin started")
        self.client.initialise(self.message_handler,open_callback=self.open_handler,close_callback=self.close_handler,error_callback=self.error_handler)
    
    def message_handler(self, ws, data):
  

        if len(data) == 0:
                return
        race_data = json.loads(data)
        
        if "racestatus" in race_data:
            print(race_data["racestatus"].get("raceAction"))
            print(race_data["racestatus"])
            if race_data["racestatus"].get("raceAction") == "start":

                self.heat_data = []
                race = self._rhapi.race
                self._raceabort = False
                race.stage()

            if race_data["racestatus"].get("raceAction") == "abort":
                self.heat_data = []
                self._raceabort = True
                race = self._rhapi.race
                race.stop()

            elif race_data["racestatus"].get("raceAction") == "race finished" and not self._raceabort:
                self.heat_data = []
                race = self._rhapi.race
                self._raceabort = False 
                race.stop(doSave=True)

        elif "racedata" in race_data:
            for pilot_name, pilot_data in race_data["racedata"].items():
                pilot = next((e for e in self.heat_data if e["name"] == pilot_name), None)

                if pilot is None:
                    pilot = self.create_pilot(pilot_data, pilot_name)
                    self.heat_data.append(pilot)
                    
                    self.addlap(pilot_name,pilot_data["time"])
                else:
                    try:
                        if pilot["lap"] != pilot_data["lap"]:
                            pilot["laps"].append(pilot_data["time"])  
                            pilot["lap"] = pilot_data["lap"]

                            self.addlap(pilot_name,pilot_data["time"])

                        if pilot["finished"] != pilot_data["finished"]:
                            pilot["finished"] = pilot_data["finished"]
                            pilot["laps"].append(pilot_data["time"])  
                            pilot["lap"] = pilot_data["lap"]
                 
                            self.addlap(pilot_name,pilot_data["time"])


                    except Exception as e:
                        print(f"Error processing data for {pilot_name}: {e}")

    def addlap(self, pilot_name, thetime):
        race = self._rhapi.race
        starttime = race.start_time_internal
        laptime = starttime + float(thetime)
        db = self._rhapi.db
        pilots = race.pilots
        for key, value in pilots.items():
            pilotveloname = db.pilot_attribute_value(value, "velo_callsign")
            if pilotveloname is not None:
                if pilot_name == pilotveloname:
                    race.lap_add(key,laptime)
        

    def open_handler(self,ws):
        print("WebSocket connection opened.")

    def close_handler(self,ws, close_status_code, close_msg):
        print("WebSocket connection closed:")


    def error_handler(self,ws, error):
        print("WebSocket error:", error)

    
