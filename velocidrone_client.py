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

        # Start the heartbeat
        threading.Thread(target=self.heartbeat, daemon=True).start()

    def run(self):
        self.ws.run_forever()

    def heartbeat(self):
        while True:
            try:
                if self.ws and self.ws.sock.connected:
                    self.ws.send("")
                time.sleep(10)  # Send a heartbeat every 10 seconds
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break

# Example usage:
# def message_handler(ws, message):
#     print("Message received:", message)

# def open_handler(ws):
#     print("WebSocket connection opened.")

# def close_handler(ws, close_status_code, close_msg):
#     print("WebSocket connection closed:", close_msg)

# def error_handler(ws, error):
#     print("WebSocket error:", error)

# client = VelocidroneClient()
# client.initialise(
#     "settings.json",
#     message_handler,
#     open_callback=open_handler,
#     close_callback=close_handler,
#     error_callback=error_handler
# )
