# RotorHazard Velocidrone Lite - Plugin

## 1.0 Introduction 

This plugin allows RotorHazard to subscribe to Velocidrones websocket messages. These messages can be used to do the following:

* "Start", "Stop & Discard" or "Stop & Save" races from Velocidrone.
* "Start" or "Stop" races from RotorHazard.
* Activate pilots in Velocidrone. Pilots in the current heat will switch to "flying" while everyone else will switch to "spectate".
* Activation can be done automatically when changing heats or manually at the new Velocidrone Control Panael. 
* During a race, detect the holeshot and add to RotorHazard
* During a race, add laps to RotorHazard 
* Allow race director to enter IP address of Velocidrone from Settings page
* Allow race director to import the csv file exported from Velocidrone leaderboard.
* Support for tracks with start/stop gate checked. Both lap times and total times will be in RotorHazard.
* Tracks with different start stop gates are only able to get lap times and not total times.
* Allow auto save or manual save setting when game is complete
* NOTE: This has been updated to only work with the upcoming release. Currently in Beta. 

## 2.0 Installation

1. Download the zip folder, unzip it and place in the RotorHazard "Plugins" folder.
2. Execute the following command to install Web Socket dependency

```
pip install websocket-client
```
3. Restart RotorHazard.

## 3.0 User Guide

# Connecting to the Velocidrone websocket.
1. On Velocidrone home screen, click on "Options" and on the "Main Settings" tab, search for "Websocket Communication". Switch this to "Yes"
<img width="853" alt="Screenshot 2025-01-27 at 5 57 47 PM" src="https://github.com/user-attachments/assets/276a201d-c85f-4028-b52b-b9bcbbd0e158" />

2. On RotorHazard, head over to the "run" page and look for the newly created "Velocidrone Controls" panel. Enter the IP address of the machine where Velocidrone is running from.
3. Hit Connect to establish a websocket. This only works if Velocidrone is running. Disconnect anytime.


<img width="878" alt="Screenshot 2025-01-29 at 8 14 13 PM" src="https://github.com/user-attachments/assets/292acd4d-2d48-4206-8139-42e0bcdf9c00" />


# Importing pilots 
4. To import pilots from Velocidrone, head over to the "Format" page and scroll down to "Data Management" panel.
5. The "Importer" drop down on the left now contains a new importer called "Velocidrone Pilot Import CSV". Have this selected.
6. Select the CSV file downloaded from Velocidrone leaderboard.
7. Hit the "Import Data". Select if the following check box to wipe out existing list of pilots or update.
![Screenshot 2025-01-27 at 5 58 25 PM](https://github.com/user-attachments/assets/dc10a3a8-83cb-4083-89c3-464d2ac03384)


8. Thats it. Now create heats on RotorHazard as per usual...... 
