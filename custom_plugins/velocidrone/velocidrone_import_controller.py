
import logging
from RHUI import UIField, UIFieldType
from data_import import DataImporter
import csv

class VeloImportController:

    def __init__(self, rhapi):
        self._IMPORT_LABEL = 'Velocidrone Pilot Import CSV'
        self._rhapi = rhapi
        self.logger = logging.getLogger(__name__)

    def init_importer(self,args):

        for importer in [
            DataImporter(self._IMPORT_LABEL,self.import_csv,None,[UIField('reset_pilots', "Reset all pilots", UIFieldType.CHECKBOX, value=True),]),
        ]:
            args['register_fn'](importer)


    def import_csv(self,importer_class, rhapi, source, args):
        if not source:
            return False

        try:
            rows = self.parse_csv(source)
        except Exception as ex:
            print("Unable to import file: {}".format(str(ex)))
            return False

        self.logger.debug("Importing from CSV...")

        if 'reset_pilots' in args and args['reset_pilots']:
            self._rhapi.db.pilots_reset()

        for row in rows:
            try:
                v_player_name = row["Player Name"]
                v_user_id = row["Userid"]

                # Simple validation
                if not v_player_name or not v_user_id:
                    self.logger.warning(f"Skipping row with missing Player Name or Userid: {row}")
                    continue

                # Check if a pilot with this VelociDrone ID already exists
                existing_pilot = self.find_pilot_by_velocidrone_uid(v_user_id)

                if existing_pilot:
                    # If you want to update their info, do it here.
                    # Example: Update callsign to match CSV's Player Name
                    self._rhapi.db.pilot_alter(existing_pilot.id, callsign=v_player_name)
                    self.logger.info(
                        f"Updated pilot {existing_pilot.id} with new callsign={v_player_name}"
                        f" (VelociDrone UID={v_user_id})"
                    )
                else:
                    # Create a new pilot in RotorHazard
                    new_pilot = self._rhapi.db.pilot_add(
                        name=v_player_name,       # "Name" in RotorHazard
                        callsign=v_player_name    # "Callsign" in RotorHazard
                    )
                    # Store VelociDrone ID as pilot attribute
                    self._rhapi.db.pilot_alter(new_pilot.id, attributes={
                        'velo_uid': v_user_id
                    })
                    self.logger.info(
                        f"Created new pilot: Player Name={v_player_name}, "
                        f"VelociDrone UID={v_user_id}")
            except KeyError as ex:
                # This means the CSV is missing one or more required columns
                self.logger.error(f"CSVImportPlugin: Missing expected column: {ex}")
            except Exception as ex:
                self.logger.error(f"CSVImportPlugin: Error processing row {row}: {ex}")
            

        self.logger.debug("CSV import completed.")
        return True

    def find_pilot_by_velocidrone_uid(self, uid_value):

        for pilot in self._rhapi.db.pilots:
            stored_uid = self._rhapi.db.pilot_attribute_value(pilot.id, 'velo_uid', None)
            if stored_uid == uid_value:
                return pilot
        return None
    
    def parse_csv(self,source):

        rows = []
        try:
            # Ensure the source is treated as a text stream
            if isinstance(source, bytes):
                source = source.decode("utf-8")
            reader = csv.DictReader(source.splitlines())
            for row in reader:
                rows.append(row)
        except Exception as ex:
            self.logger.error("Error parsing CSV: {}".format(str(ex)))
            raise
        return rows