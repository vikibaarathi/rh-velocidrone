# RotorHazard Velocidrone Lite - Plugin

## 1.0 Introduction 

This plugin allows RotorHazard to subscribe to Velocidrones websocket messages. These messages can be used to do the following:

* "Start", "Stop & Discard" or "Stop & Save" races in RH from Velocidrone.
* Read pilot name and compare with pilot list in RH.
* Add lap if pilot match found to current existing heat. 
* Allow race director to start & stop the websocket. - WIP
* Allow race director to enter IP address of Velocidrone from UI - WIP (Currently its hardcoded)

## 2.0 Installation

1. Download the zip folder, unzip it into the plugins folder within RotorHazard.
2. Install the websocket client in Terminal
```
pip install websocket-client

```
3. Restart RotorHazard.
4. A new panel will appear in Settings page. Enter the IP address of where Velocidrone is running. 
![Screenshot 2025-01-26 at 9 48 02 PM](https://github.com/user-attachments/assets/9f308d98-e596-4dd1-b492-16825bdb5b24)

## Note

This is just a prototype and not an ideal solution as the callsign is used to map with the pilots within RH. 
