# Velocidrone RotorHazard Plugin

## 1.0 Introduction & Minimum Requirements

### 1.1 Introduction
This plugin allows RotorHazard to subscribe to Velocidrones websocket messages. These messages can be used to do the following:

* "**Start**", "**Stop & Discard**" or "**Stop & Save**" races from Velocidrone.
* "**Start**" or "Stop" races from RotorHazard.
* Activate pilots in Velocidrone. Pilots in the current heat will switch to "flying" while everyone else will switch to "spectate".
* Activation can be done automatically when changing heats or manually at the Velocidrone Control Panael within the "**Run**" page. 
* Adds holeshot / laps to RotorHazard.
* Allow race director to enter IP address of Velocidrone from Settings page.
* Allow race director to import the csv file exported from Velocidrone leaderboard.
* Allow auto save or manual save setting when game is complete.
* Allow up to 8 pilots to fly at the same time.
* Important Note:  **Support for tracks with start/stop gate checked.**

### 1.2 Minimum Requirements

1.2.1. Have latest RotorHazard 4.2 and above installed on a timer or on a laptop. Installations instrutions are available at http://rotorhazard.com.
1.2.2. Track in velocidrone must have the Start & Stop gate checked. Support for different Start & Stop gates will be coming in next release. 

## 2.0 Installation

1. Have RotorHazard 4.1 and above installed and running on a computer or a timer.
2. RotorHazard & Velocidrone must be in the same network or same machine. 
3. Download the zip folder, unzip it and place in the RotorHazard "Plugins" folder: `/src/server/plugins`
4. Execute the following command to install Web Socket dependency

```
pip install websocket-client
```
5. Restart RotorHazard.
6. Head over to settings -> plugins to verify plugin installation.

<img width="1054" alt="Screenshot 2025-01-29 at 9 12 33 PM" src="https://github.com/user-attachments/assets/11319e86-d9ae-418a-aa1c-58fdc65b797d" />
7. For more information on RotorHazard and the plugins mechanism, please check out the [RotorHazard Page](https://github.com/RotorHazard/RotorHazard)

## 3.0 User Guide

### 3.1 Connecting to the Velocidrone websocket.
1. On Velocidrone home screen, click on "Options" and on the "Main Settings" tab, search for "Websocket Communication". Switch this to "Yes"
<img width="853" alt="Screenshot 2025-01-27 at 5 57 47 PM" src="https://github.com/user-attachments/assets/276a201d-c85f-4028-b52b-b9bcbbd0e158" />

2. On RotorHazard, head over to the "run" page and look for the newly created "Velocidrone Controls" panel. Enter the IP address of the machine where Velocidrone is running from.
3. Hit Connect to establish a websocket. This only works if Velocidrone is running. Disconnect anytime.


<img width="878" alt="Screenshot 2025-01-29 at 8 14 13 PM" src="https://github.com/user-attachments/assets/292acd4d-2d48-4206-8139-42e0bcdf9c00" />



### 3.2 Importing pilots 
1. To import pilots from Velocidrone, head over to the "Format" page and scroll down to "Data Management" panel.
2. The "Importer" drop down on the left now contains a new importer called "Velocidrone Pilot Import CSV". Have this selected.
3. Select the CSV file downloaded from Velocidrone leaderboard.
4. Hit the "Import Data". Select if the following check box to wipe out existing list of pilots or update.
![Screenshot 2025-01-27 at 5 58 25 PM](https://github.com/user-attachments/assets/dc10a3a8-83cb-4083-89c3-464d2ac03384)
5. Pilots can be added manually as well at the "Format" page. Make sure the Velocidrone ID is entered.
6. TODO: MultiGP RaceSync pilot matching.

### 3.3. Run a race
1. Run races as per usual using RotorHazard. As long the Velocidrone ID is available, the laps will trigger in RH>
2. Start or stop a race from either RH or Velocidrone. Both will work.
3. Upon each lap complete, laps will be added in RH as long as the Velocidrone ID matches the pilots in RH.
4. When a race completes, laps can be saved automatically or manually. Auto heat change is configured in RH itself.
5. Activating pilots is an option. If selected, heat change will trigger activation or when pressing the "re-active" button. 


