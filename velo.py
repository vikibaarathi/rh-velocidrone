import json
import requests
import logging
from sqlalchemy.ext.declarative import DeclarativeMeta
from RHUI import UIField, UIFieldType
from .datamanager import ClDataManager
from .velocidrone_client import VelocidroneClient
import time
class Velo():

    heat_data = []

    def __init__(self,rhapi):
        self.logger = logging.getLogger(__name__)
        self._rhapi = rhapi
        self.startsocket(rhapi)

    def create_pilot(self,pilot_data, pilot_name):
        return {
            "name": pilot_name,
            "holeshot": pilot_data["time"],
            "laps": [pilot_data["time"]],
            "lap": pilot_data["lap"]
        }
    def startsocket(self,args):
        print("Hello World: Velocidrone")
        race = self._rhapi.race
        racestarttime = race.start_time_internal
        print(racestarttime)

        client = VelocidroneClient()
        client.initialise(
            "settings.json",
            self.message_handler,
            open_callback=self.open_handler,
            close_callback=self.close_handler,
            error_callback=self.error_handler
        )

        
    def startrace(self,args):
        print(args)
        monotonic_time = time.monotonic()
        laptime = monotonic_time + 1
        race = self._rhapi.race
        # race.lap_add(0,laptime)

        print(monotonic_time)
    
    def message_handler(self, ws, data):
        if len(data) == 0:
                return

        race_data = json.loads(data)
        if "racestatus" in race_data:
            print(race_data["racestatus"].get("raceAction"))
            if race_data["racestatus"].get("raceAction") == "start":
                self.heat_data = []

        elif "racedata" in race_data:
            for pilot_name, pilot_data in race_data["racedata"].items():
                pilot = next((e for e in self.heat_data if e["name"] == pilot_name), None)

                if pilot is None:
                    pilot = self.create_pilot(pilot_data, pilot_name)
                    self.heat_data.append(pilot)
                    print(pilot)
                    if pilot_name == "JiaJia_FPV":
                        self.addlap(0,pilot_data["time"])
                else:
                    try:
                        if pilot["lap"] != pilot_data["lap"]:
                            pilot["laps"].append(pilot_data["time"])  # Convert to float
                            pilot["lap"] = pilot_data["lap"]
                            print(pilot)
                            if pilot_name == "OMNI FPV":
                                self.addlap(0,pilot_data["time"])

                            if pilot_name == "JiaJia_FPV":
                                self.addlap(1,pilot_data["time"])

                    except Exception as e:
                        print(f"Error processing data for {pilot_name}: {e}")

    def addlap(self, index, thetime):
        race = self._rhapi.race
        monotonic_time = time.monotonic()

        starttime = race.start_time_internal

        laptime = starttime + float(thetime)
        
        race.lap_add(index,laptime)

    def open_handler(self,ws):
        print("WebSocket connection opened.")

    def close_handler(self,ws, close_status_code, close_msg):
        print("WebSocket connection closed:", close_msg)

    def error_handler(self,ws, error):
        print("WebSocket error:", error)

    
