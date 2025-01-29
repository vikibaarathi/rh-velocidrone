import logging
import json
from .velocidrone_websocket_manager import VeloWebsocketManager
from RHUI import UIField, UIFieldType

class Pilot:
    def __init__(self, uid, name, lap=0, finished=False, last_crossing_time=0.0):
        self.uid = uid
        self.name = name
        self.lap = lap
        self.finished = finished
        self.laps = []
        self.last_crossing_time = last_crossing_time

    def add_time_of_gate(self, time):
        self.laps.append(time)
        self.lap = self.lap + 1

    def mark_finished(self):
        self.finished = True
        if self.lap == 1:
            self.lap = 2

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
    #REMOVE THIS WHOLE THING
    # def create_pilot(self,pilot_data, pilot_name):
    #     return {
    #         "name": pilot_name,
    #         "holeshot": pilot_data["time"],
    #         "laps": [pilot_data["time"]],
    #         "lap": int(pilot_data["lap"]),
    #         "finished": pilot_data.get("finished", "False").lower() == "true",
    #         "uid": pilot_data["uid"],
    #         "last_crossing_time": 0.0
    #     }  

    def start_socket(self, args):
        ip_address = self._rhapi.db.option("velo-field-ip")
        if not ip_address:
            self._rhapi.ui.message_notify("IP Address is required")
            return
        self.logger.info("Establishing Velocidrone connection.")
        self.vwm.initialise(ip_address,message_callback=self.message_handler,open_callback=self.open_handler,close_callback=self.close_handler,error_callback=self.error_handler)

    def stop_socket(self, args):
        self.logger.info("Stopping Velocidrone websocket connection")
        self.vwm.disconnect(args)
        return
    

    def message_handler(self,ws, data):
        if not data:
            return
        try:
            race_data = json.loads(data)
            #self.logger.debug(f"Received Race Data: {race_data}")
            self.process_race_data(race_data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding race data: {e}")

    def process_race_data(self, race_data):
        if "FinishGate" in race_data:
            self._start_finish_gate = race_data["FinishGate"].get("StartFinishGate", "false").lower() == "true"
        elif "racestatus" in race_data:
            self.handle_race_status(race_data["racestatus"])
        elif "racedata" in race_data:
            self.handle_race_data(race_data["racedata"])

    def handle_race_status(self, status):
        race = self._rhapi.race
        action = status.get("raceAction", "").lower()
        if action == "start":
            self.heat_data.clear()
            self._raceabort = False
            race.stage()
        elif action == "abort":
            self.heat_data.clear()
            self._raceabort = True
            race.stop()
        elif action == "race finished" and not self._raceabort:
            self.heat_data.clear()
            self._raceabort = False
            race.stop(doSave=True)

    def handle_race_data(self, race_data):
        for pilot_name, pilot_data in race_data.items():
            pilot = next((p for p in self.heat_data if p.name == pilot_name), None)
            if not pilot:
                pilot = Pilot(uid=pilot_data["uid"], name=pilot_name, lap=int(pilot_data["lap"]))
                self.heat_data.append(pilot)

                ## NEED TO IMPLEMENT THIS METHOD
                self.add_lap(pilot.uid, float(pilot_data["time"]))
            else:

                ## HERE COMES THE HARD PART
                self.process_pilot_lap(pilot, pilot_data, pilot_name)

    def process_pilot_lap(self, pilot:Pilot, pilot_data, pilot_name):
        try:
            time = float(pilot_data["time"])
            new_lap = int(pilot_data["lap"])
            finished = pilot_data.get("finished", "false").lower() == "true"
            
            # FOR START/STOP CHECKED
            if self._start_finish_gate:
                if new_lap > pilot.lap:
                    pilot.add_time_of_gate(time)
                    self.add_lap(pilot.uid, time)

                if not pilot.finished and finished:
                    pilot.mark_finished()
                    self.add_lap(pilot.uid, time)

            else: #FOR START/ STOP UNCHECKED

                current_gate = int(pilot_data["gate"])
                finished_value = pilot_data["finished"]
                is_finished = finished_value.lower() == 'true'

                if current_gate > 1:
                    pilot.add_time_of_gate(time)
                    
                if current_gate == 1 and new_lap == 2:
                    laptime = pilot.laps[-1]
                    pilot.last_crossing_time = time - laptime
                    self.add_lap(pilot.uid, laptime)
                    pilot.laps.clear()
                    pilot.add_time_of_gate(time)
                                        
                if current_gate == 1 and new_lap > 2:
                    laptime = pilot.laps[-1] - pilot.last_crossing_time
                    self.add_lap(pilot.uid, laptime)
                    pilot.last_crossing_time = pilot.last_crossing_time + time - pilot.laps[-1]
                    pilot.laps.clear()
                    pilot.add_time_of_gate(time)

                if is_finished:
                    laptime = time - pilot.last_crossing_time
                    self.add_lap(pilot.uid, laptime)
                    pilot.laps.clear()
                    pilot.last_crossing_time = 0.0

        except Exception as e:
            self.logger.error(f"Error processing data for {pilot.name}: {e}")

    def add_lap(self, pilot_uid, time):
        race = self._rhapi.race
        start_time = race.start_time_internal
        lap_time = start_time + time
        
        db = self._rhapi.db
        pilots = race.pilots
        for key, value in pilots.items():
            if db.pilot_attribute_value(value, "velo_uid") == str(pilot_uid):
                race.lap_add(key, lap_time)
                return


    #NEED TO REMOVE THIS LATER
    # def message_handler(self, ws, data):
  

    #     if len(data) == 0:
    #             return
    #     race_data = json.loads(data)

    #     print(f"[DEBUG] Race Data: {race_data}")

    #     if "FinishGate" in race_data:
    #         self._start_finish_gate = race_data["FinishGate"].get("StartFinishGate").lower() == "true"

        
    #     elif "racestatus" in race_data:

    #         if race_data["racestatus"].get("raceAction") == "start":

    #             self.heat_data = []
    #             race = self._rhapi.race
    #             self._raceabort = False
    #             race.stage()

    #         if race_data["racestatus"].get("raceAction") == "abort":
    #             self.heat_data = []
    #             self._raceabort = True
    #             race = self._rhapi.race
    #             race.stop()

    #         elif race_data["racestatus"].get("raceAction") == "race finished" and not self._raceabort:
    #             self.heat_data = []
    #             race = self._rhapi.race
    #             self._raceabort = False 
    #             race.stop(doSave=True)

    #     elif "racedata" in race_data:
    #         for pilot_name, pilot_data in race_data["racedata"].items():
    #             pilot = next((e for e in self.heat_data if e["name"] == pilot_name), None)

    #             if pilot is None:
                    
    #                 pilot = self.create_pilot(pilot_data, pilot_name)
    #                 self.heat_data.append(pilot)
    #                 time = float(pilot_data["time"])
    #                 self.addlap(pilot_data["uid"], time)
                    
    #             else:

    #                 try:

    #                     time = float(pilot_data["time"])  # cumulative race time
    #                     new_lap = int(pilot_data["lap"])  # Convert lap to integer
    #                     finished = pilot_data["finished"].lower() == "true"

    #                     if self._start_finish_gate:
    #                         # Handle start/finish gate scenario
    #                         if new_lap > pilot["lap"]:  # Ensure new_lap is an integer
    #                             if pilot["lap"] == 0 and new_lap == 1:
    #                                 pilot["lap"] = 1
                                   
    #                             else:
    #                                 pilot["lap"] = new_lap
    #                                 pilot["laps"].append(time)
    #                                 self.addlap(pilot_data["uid"], time)

    #                         if not pilot["finished"] and finished:
    #                             #print(f"[DEBUG] Finished Pilot: {pilot}")
    #                             pilot["finished"] = True
    #                             #print(f"[DEBUG] {pilot_name} finished race at {time:.3f}s")
    #                             if pilot["lap"] == 1:
    #                                 pilot["lap"] = 2
    #                                 pilot["laps"].append(time)
    #                                 #print(f"[DEBUG] Single-lap scenario for {pilot_name}, recorded final lap at {time:.3f}s")
    #                             self.addlap(pilot_data["uid"], time)

    #                     else:

    #                         current_gate = int(pilot_data["gate"])
    #                         finished_value = pilot_data["finished"]
    #                         is_finished = finished_value.lower() == 'true'

    #                         if current_gate > 1:
    #                             pilot["laps"].append(time)
                                
    #                         if current_gate == 1 and new_lap == 2:
   
    #                             pilot["last_crossing_time"] = time - pilot["laps"][-1]
    #                             race = self._rhapi.race
    #                             starttime = race.start_time_internal     
    #                             lap4time = pilot["laps"][-1]

    #                             flaptime = starttime +  lap4time
    #                             pilotuid = pilot["uid"]
    #                             db = self._rhapi.db
    #                             pilots = race.pilots
    #                             for key, value in pilots.items():
    #                                 pilotveloid = db.pilot_attribute_value(value, "velo_uid")
    #                                 if pilotveloid is not None:
    #                                     if str(pilotuid) == str(pilotveloid):
    #                                         print(pilot_name)
    #                                         print(pilotveloid)
    #                                         race.lap_add(key,flaptime)

    #                             pilot["laps"] = []
    #                             pilot["laps"].append(time)
                                                  
    #                         if current_gate == 1 and new_lap > 2:
                                
    #                             race = self._rhapi.race
    #                             starttime = race.start_time_internal
                                
    #                             lap4time = pilot["laps"][-1] - pilot["last_crossing_time"]
                                
    #                             pilot["last_crossing_time"] = pilot["last_crossing_time"] + time - pilot["laps"][-1]
    #                             flaptime = starttime +  lap4time
    #                             pilotuid = pilot["uid"]
    #                             db = self._rhapi.db
    #                             pilots = race.pilots
    #                             for key, value in pilots.items():
    #                                 pilotveloid = db.pilot_attribute_value(value, "velo_uid")
    #                                 if pilotveloid is not None:
    #                                     if str(pilotuid) == str(pilotveloid):
    #                                         print(pilot_name)
    #                                         print(pilotveloid)
    #                                         race.lap_add(key,flaptime)


    #                             pilot["laps"] = []
    #                             pilot["laps"].append(time)

    #                         if is_finished:
    #                             print("Handling final lap")
                            
    #                             laptime = time - pilot["last_crossing_time"]

    #                             race = self._rhapi.race
    #                             starttime = race.start_time_internal
    #                             print(starttime)
    #                             flaptime = starttime + laptime
    #                             print(flaptime)

    #                             pilotuid = pilot["uid"]
    #                             db = self._rhapi.db
    #                             pilots = race.pilots
    #                             for key, value in pilots.items():
    #                                 pilotveloid = db.pilot_attribute_value(value, "velo_uid")
    #                                 if pilotveloid is not None:
    #                                     if str(pilotuid) == str(pilotveloid):
    #                                         print(pilot_name)
    #                                         print(pilotveloid)
    #                                         race.lap_add(key,flaptime)

    #                             pilot["laps"] = []
    #                             pilot["last_crossing_time"] = 0.0

    #                 except Exception as e: print(f"Error processing data for {pilot_name}: {e}")


    # def addlap(self, pilot_name, thetime):
    #     print("add lap for pilot")
    #     race = self._rhapi.race
    #     starttime = race.start_time_internal
    #     print(starttime)
    #     laptime = starttime + float(thetime)
 
    #     db = self._rhapi.db
    #     pilots = race.pilots
    #     for key, value in pilots.items():
    #         pilotveloname = db.pilot_attribute_value(value, "velo_uid")
    #         if pilotveloname is not None:
    #             if str(pilot_name) == str(pilotveloname):
    #                 print(pilot_name)
    #                 print(pilotveloname)
    #                 race.lap_add(key,laptime)

    def open_handler(self, ws):
        msg = "WebSocket connection opened."
        self._rhapi.ui.message_notify("WebSocket connection opened.")
        self.logger.info(msg)

    def close_handler(self, ws, close_status_code, close_msg):
        msg = "Websocket connection closed:" 
        self._rhapi.ui.message_notify(msg)
        self.logger.info(msg)

    def error_handler(self, ws, error):
        msg = "Websocket connection closed"
        self._rhapi.ui.message_notify(msg)
        self.logger.info(msg)

    def start_race_from_rh(self,args):
        print("Starting velocidrone race from RH")
        payload = {"command": "startrace"}
        self.send_command(payload)
    
    def stop_race_from_rh(self,args):
        print("Starting velocidrone race from RH")
        payload = {"command": "abortrace"}
        self.send_command(payload)

    def set_current_heat(self,args):
        print("Heat changed, sending current heat pilots to velocidrone")
        print(args)
        list_of_uid = []
        race = self._rhapi.race
        pilots = race.pilots
        db = self._rhapi.db
        for key, pilot_id in pilots.items():
            pilot_uid = db.pilot_attribute_value(pilot_id, "velo_uid")
            if pilot_uid:
                list_of_uid.append(pilot_uid)
        print(list_of_uid)
        payload = {"command": "activate","pilots": list_of_uid}
        self.send_command(payload)

    def send_command(self, payload):
        message = json.dumps(payload)
        self.vwm.send_message(message)