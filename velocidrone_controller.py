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
        self._start_finish_gate = False
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
            "laps": [],
            "lap": int(pilot_data["lap"]),
            "finished": pilot_data.get("finished", "False").lower() == "true",
            "uid": pilot_data["uid"],
            "last_crossing_time": 0.0
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

        print(f"[DEBUG] Race Data: {race_data}")

        if "FinishGate" in race_data:
            self._start_finish_gate = race_data["FinishGate"].get("StartFinishGate").lower() == "true"
            #print(f"startFinishGate set to {self._start_finish_gate}")
        
        elif "racestatus" in race_data:
            #print(race_data["racestatus"].get("raceAction"))
            #print(race_data["racestatus"])
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
                    print(f"[DEBUG] Pilot not found: {pilot}, Pilot Data: {pilot_data}")
                    pilot = self.create_pilot(pilot_data, pilot_name)
                    self.heat_data.append(pilot)

                    time = float(pilot_data["time"])
                    print("holeshot")
                    print(pilot_data["uid"])
                    print(time)
                    self.addlap(pilot_data["uid"], time)
                else:
                    #print(f"[DEBUG] Pilot found: {pilot}, Pilot Data: {pilot_data}")

                    # Process lap data based on start_finish_gate

                    try:

                        time = float(pilot_data["time"])  # cumulative race time
                        new_lap = int(pilot_data["lap"])  # Convert lap to integer
                        finished = pilot_data["finished"].lower() == "true"

                        if self._start_finish_gate:
                            # Handle start/finish gate scenario
                            if new_lap > pilot["lap"]:  # Ensure new_lap is an integer
                                if pilot["lap"] == 0 and new_lap == 1:
                                    pilot["lap"] = 1
                                    #print(f"[DEBUG] {pilot_name} (start_finish_gate=TRUE) started lap 1 at {time:.3f}s")
                                else:
                                    pilot["lap"] = new_lap
                                    pilot["laps"].append(time)
                                    completed_lap = new_lap - 1
                                    #print(f"[DEBUG] {pilot_name} (start_finish_gate=TRUE) completed lap {completed_lap} at {time:.3f}s")
                                    self.addlap(pilot_data["uid"], time)

                            if not pilot["finished"] and finished:
                                #print(f"[DEBUG] Finished Pilot: {pilot}")
                                pilot["finished"] = True
                                #print(f"[DEBUG] {pilot_name} finished race at {time:.3f}s")
                                if pilot["lap"] == 1:
                                    pilot["lap"] = 2
                                    pilot["laps"].append(time)
                                    #print(f"[DEBUG] Single-lap scenario for {pilot_name}, recorded final lap at {time:.3f}s")
                                    self.addlap(pilot_data["uid"], time)

                        else:
                            # Handle separate start and finish gates
                            if abs(pilot["last_crossing_time"]) < 1e-5:
                                pilot["last_crossing_time"] = time

                            if new_lap > pilot["lap"]:  # Ensure new_lap is an integer
                                if pilot["lap"] == 0 and new_lap == 1:
                                    pilot["lap"] = 1
                                else:
                                    completed_lap_time = pilot["last_crossing_time"]
                                    pilot["lap"] = new_lap
                                    pilot["laps"].append(completed_lap_time)
                                    completed_lap = new_lap - 1
                                    #print(f"[DEBUG] {pilot_name} (start_finish_gate=FALSE) completed lap {completed_lap} at {completed_lap_time:.3f}s")
                                    self.addlap(pilot_data["uid"], completed_lap_time)

                            pilot["last_crossing_time"] = time

                            #print(f"[DEBUG] Finished Pilot: {bool(pilot["finished"])} and Finished pilot Data: {finished} ")
                            if not pilot["finished"] and finished:
                                #print(f"[DEBUG] Finished Pilot: {pilot}")
                                pilot["finished"] = True
                                pilot["laps"].append(time)
                                just_finished_lap = pilot["lap"] if pilot["lap"] != 0 else 1
                                #print(f"[DEBUG] {pilot_name} finished race at {time:.3f}s on lap {just_finished_lap}")
                                self.addlap(pilot_data["uid"], time)

                    except Exception as e: print(f"Error processing data for {pilot_name}: {e}")

    def addlap(self, pilot_name, thetime):
        print("add lap for pilot")
        race = self._rhapi.race
        starttime = race.start_time_internal
        laptime = starttime + float(thetime)
        db = self._rhapi.db
        pilots = race.pilots
        for key, value in pilots.items():
            pilotveloname = db.pilot_attribute_value(value, "velo_uid")
            if pilotveloname is not None:
                print(pilot_name)
                print(pilotveloname)
                if str(pilot_name) == str(pilotveloname):
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

    