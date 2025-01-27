import logging
import json
from .velocidrone_websocket_manager import VeloWebsocketManager
from RHUI import UIField, UIFieldType

class VeloController:
    
    def __init__(self, rhapi):
        self._rhapi = rhapi
        self.logger = logging.getLogger(__name__)

        self.vwm = VeloWebsocketManager()
        self.heat_data = []
        self._raceabort = False
        
    def init_ui(self, args):
        VELO_PLUGIN_ID = "velocidrone-plugin"

        fields = self._rhapi.fields

        # Register a custom pilot attribute in pilot section
        velo_uid_attribute = UIField(name="velo_uid", label="Velocidrone UID", field_type=UIFieldType.TEXT)
        fields.register_pilot_attribute(velo_uid_attribute)

        # Create a new panel and set of UI elements
        ui = self._rhapi.ui
        ui.register_panel(VELO_PLUGIN_ID, "Velocidrone Websockets", "settings")

        # Create buttons to start and stop the websocket connection
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-connect", "Connect Websocket", self.start_socket)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-disconnect", "Disconnect Websocket", self.stop_socket)

        # Input for the IP address
        velo_ip_address = UIField(name = "velo-field-ip", label = "Velocidrone IP Address", field_type = UIFieldType.TEXT, desc = "The IP address of where Velocidrone is running")  
        fields.register_option(velo_ip_address, VELO_PLUGIN_ID)

    def create_pilot(self,pilot_data, pilot_name):
        return {
            "name": pilot_name,
            "holeshot": pilot_data["time"],
            "laps": [pilot_data["time"]],
            "lap": pilot_data["lap"],
            "finished": pilot_data["finished"]
        }    

    def start_socket(self, args):
        ip_address = self._rhapi.db.option("velo-field-ip")

        if ip_address == None or ip_address == "":
            msg = "IP Address is required"
            self._rhapi.ui.message_notify(msg)
            return
        else:
            print("Velocidrone plugin started")
            self.vwm.initialise(ip_address,message_callback=self.message_handler,open_callback=self.open_handler,close_callback=self.close_handler,error_callback=self.error_handler)

    def stop_socket(self, args):
        self.vwm.disconnect(args)
        return

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
            pilotveloname = db.pilot_attribute_value(value, "velo_uid")
            if pilotveloname is not None:
                if pilot_name == pilotveloname:
                    race.lap_add(key,laptime)

    def open_handler(self, ws):
        msg = "WebSocket connection opened."
        self._rhapi.ui.message_notify(msg)
        print(msg)

    def close_handler(self, ws, close_status_code, close_msg):
        msg = "Websocket connection closed:" 
        self._rhapi.ui.message_notify(msg)
        print(msg)

    def error_handler(self, ws, error):
        msg = "Websocket connection closed"
        self._rhapi.ui.message_notify(msg)
        print(msg)

    