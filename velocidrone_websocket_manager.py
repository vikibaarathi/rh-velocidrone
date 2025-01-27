import threading
import time
from websocket import WebSocketApp

class VeloWebsocketManager:
    def __init__(self):
        self.ws = None
        self.ws_thread = None
        self.ping_thread = None
        self._is_running = False

    def initialise(self, ip_address, message_callback, open_callback=None, close_callback=None, error_callback=None):
        uri = f"ws://{ip_address}:60003/velocidrone"
        self.ws = WebSocketApp(
            uri,
            on_message=message_callback,
            on_open=open_callback,
            on_close=close_callback,
            on_error=error_callback
        )
        self._is_running = True
        self._start_threads()

    def _start_threads(self):
        # Run the WebSocket client in a separate thread
        self.ws_thread = threading.Thread(target=self._run, daemon=True)
        self.ws_thread.start()

        # Start a ping thread to keep the connection alive
        self.ping_thread = threading.Thread(target=self._send_pings, daemon=True)
        self.ping_thread.start()

    def _run(self):
        self.ws.run_forever()

    def _send_pings(self):
        while self._is_running:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send("")  # Send a ping
            time.sleep(5)

    def disconnect(self, args):
        # Stop the ping thread
        self._is_running = False

        # Close the WebSocket connection
        if self.ws:
            self.ws.close()

        # Wait for threads to exit (optional)
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join()
        if self.ping_thread and self.ping_thread.is_alive():
            self.ping_thread.join()

        print("WebSocket connection closed.")