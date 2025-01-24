import json
import threading
import time
import os
from websocket import WebSocketApp

class VelocidroneClient:
    def __init__(self):
        self.ws = None


    def initialise(self, message_callback, open_callback=None, close_callback=None, error_callback=None):


        uri = f'ws://192.168.68.59:60003/velocidrone'

        # Create a WebSocket client
        self.ws = WebSocketApp(
            uri,
            on_message=message_callback,
            on_open=open_callback,
            on_close=close_callback,
            on_error=error_callback
        )

        # Run the WebSocket client in a separate thread
        self.ws_thread = threading.Thread(target=self.run)
        self.ws_thread.daemon = True
        self.ws_thread.start()

         # Start a ping thread to keep the connection alive
        self.ping_thread = threading.Thread(target=self.send_pings)
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def run(self):
        self.ws.run_forever()

    def send_pings(self):
        while True:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send("")  # Send a ping
            time.sleep(5)  # Adjust the interval as needed