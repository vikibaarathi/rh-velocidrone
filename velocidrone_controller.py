import logging
import json
from .velocidrone_websocket_manager import VeloWebsocketManager
from RHUI import UIField, UIFieldType
from .velocidrone_pilot_model import Pilot

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
        ui.register_panel(VELO_PLUGIN_ID, "Velocidrone Controls", "run")
        # Create buttons to start and stop the websocket connection
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-connect", "Connect Velocidrone", self.start_socket)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-disconnect", "Disconnect Velocidrone", self.stop_socket)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-activate", "Reactivate Pilots", self.set_current_heat)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-all-spectate", "Turn everyone to spectate", self.all_spectate)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-lock", "Lock Room", self.lock_room)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-unlock", "Unlock Room", self.unlock_room)
        ui.register_quickbutton(VELO_PLUGIN_ID, "velo-btn-reimport", "Import pilots", self.import_pilot)

        # Input for the IP address
        velo_ip_address = UIField(name = "velo-field-ip", label = "Velocidrone IP Address", field_type = UIFieldType.TEXT, desc = "The IP address of where Velocidrone is running")  
        fields.register_option(velo_ip_address, VELO_PLUGIN_ID)

        velo_auto_save = UIField(name = 'velo-check-autosave', label = 'Auto save results', field_type = UIFieldType.CHECKBOX, desc = "Auto save results when game ends in Velocidrone")
        fields.register_option(velo_auto_save, VELO_PLUGIN_ID)

        velo_enable_activation = UIField(name = 'velo-check-enable-activation', label = 'Enable pilot activation', field_type = UIFieldType.CHECKBOX, desc = "Check this to enable pilot activation in Velocidrone based on current heat.")
        fields.register_option(velo_enable_activation, VELO_PLUGIN_ID)
        
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
            #self.logger.info(f"Received Race Data: {race_data}")
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
        elif "ActivateError" in race_data:
            self.handle_error(race_data["ActivateError"])
        elif "pilotlist" in race_data:
            self.handle_pilot_import(race_data["pilotlist"])

    def handle_pilot_import(self, pilot_list):
        db = self._rhapi.db
        for pilot in pilot_list:
            v_uid = pilot["uid"]
            callsign = pilot["name"]
            pilot_list = db.pilot_ids_by_attribute("velo_uid", v_uid)

            if len(pilot_list) == 0:
                
                new_pilot = self._rhapi.db.pilot_add(name=callsign,callsign=callsign)
                
                self._rhapi.db.pilot_alter(new_pilot.id, attributes={
                    'velo_uid': v_uid
                })
                self.logger.info(
                    f"Created new pilot: Player Name={callsign}, "
                    f"VelociDrone UID={v_uid}")
                
            else:
                self.logger.info(f"{v_uid} already exists")

    def handle_error(self, racedata):
        v_uid = racedata["UIDNotFound"]      
        db = self._rhapi.db
        pilot_list = db.pilot_ids_by_attribute("velo_uid", v_uid)

        if pilot_list and len(pilot_list) == 1:
            pilot_id = pilot_list[0]
            pilot = db.pilot_by_id(pilot_id)
            callsign = pilot.callsign
            self.logger.info(f"Pilot not found:{callsign}")
            self._rhapi.ui.message_notify(f"{callsign} is not found on the server.")
        else:
            self.logger.warning("Mismatch of Pilot UID. Please check pilot list or reimport. ")

    def handle_race_status(self, status):
        race = self._rhapi.race
        action = status.get("raceAction", "").lower()
        if action == "start":
            self.heat_data.clear()
            self._raceabort = False
            self.logger.info("Start velocidrone race from RH")
            race.stage()
        elif action == "abort":
            self.heat_data.clear()
            self._raceabort = True
            self.logger.info("Abort velocidrone race from RH")
            race.stop()
        elif action == "race finished" and not self._raceabort:
            auto_save = self._rhapi.db.option("velo-check-autosave")
            self.heat_data.clear()
            self._raceabort = False
            self.logger.info("Race finished")
            if auto_save == "1":
                race.stop(doSave=True)
            else:
                race.stop()

    def handle_race_data(self, race_data):
        #DO FOR EACH PILOT LOOP HERE
        for pilot_name, pilot_data in race_data.items():
            pilot = next((p for p in self.heat_data if p.name == pilot_name), None)
            if not pilot:
                pilot = Pilot(uid=pilot_data["uid"], name=pilot_name, lap=int(pilot_data["lap"]))
                self.heat_data.append(pilot)

                self.logger.debug(f"Holeshot: {pilot_name}")
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
            self.logger.debug(f"Lap detected for ss-checked:{pilot_data}")
            if self._start_finish_gate:
                if new_lap > pilot.lap:
                    pilot.add_time_of_gate(time)
                    self.add_lap(pilot.uid, time)

                if not pilot.finished and finished:
                    pilot.mark_finished()
                    self.add_lap(pilot.uid, time)

            else: #FOR START/ STOP UNCHECKED
                self.logger.debug(f"Lap detected for ss-unchecked:{pilot_data}")
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
        self.logger.debug(f"Add lap for pilot UID: {pilot_uid}")
        race = self._rhapi.race
        start_time = race.start_time_internal
        lap_time = start_time + time
        
        db = self._rhapi.db
        pilots = race.pilots
        for key, value in pilots.items():
            if db.pilot_attribute_value(value, "velo_uid") == str(pilot_uid):
                race.lap_add(key, lap_time)
                return

    def open_handler(self, ws):
        msg = "WebSocket connection opened."
        self._rhapi.ui.message_notify("WebSocket connection opened.")
        self.logger.info(msg)

    def close_handler(self, ws, close_status_code, close_msg):
        msg = "Websocket connection closed" 
        self._rhapi.ui.message_notify(msg)
        self.logger.info(msg)

    def error_handler(self, ws, error):
        msg = "Websocket connection closed"
        self._rhapi.ui.message_notify(msg)
        self.logger.info(msg)

    def start_race_from_rh(self,args):
        self.logger.info("Starting velocidrone race from RH")
        payload = {"command": "startrace"}
        self.send_command(payload)
    
    def stop_race_from_rh(self,args):
        self.logger.info("Starting velocidrone race from RH")
        payload = {"command": "abortrace"}
        self.send_command(payload)

    def all_spectate(self,args):
        payload = {"command": "allspectate"}
        self._rhapi.ui.message_notify("Turning all pilots to spectate")
        self.send_command(payload)
    
    def lock_room(self,args):
        payload = {"command": "lock"}
        self._rhapi.ui.message_notify("Locking room")
        self.send_command(payload)

    def unlock_room(self,args):
        payload = {"command": "unlock"}
        self._rhapi.ui.message_notify("Unlocking room")
        self.send_command(payload)

    def import_pilot(self,args):
        payload = {"command": "getpilots"}
        self._rhapi.ui.message_notify("Importing pilots")
        self.send_command(payload)
        return

    def set_current_heat(self,args):
        activation_setting = self._rhapi.db.option("velo-check-enable-activation")
        if activation_setting == "1":
            self.logger.info("Heat changed, sending current heat pilots to velocidrone")
            list_of_uid = []
            race = self._rhapi.race
            pilots = race.pilots
            db = self._rhapi.db
            for key, pilot_id in pilots.items():
                pilot_uid = db.pilot_attribute_value(pilot_id, "velo_uid")
                if pilot_uid:
                    list_of_uid.append(pilot_uid)
            payload = {"command": "activate","pilots": list_of_uid}
            result = self.send_command(payload)
            if result:
                self._rhapi.ui.message_notify("Pilots in this heat activated. ")

    def send_command(self, payload):
        message = json.dumps(payload)
        result = self.vwm.send_message(message)
        if not result:
            self._rhapi.ui.message_notify("Unable to communicate with velocidrone. Check connection.")
            return False
        return True