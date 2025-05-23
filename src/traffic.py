import threading
import time

class TunnelTraffic:
    def __init__(self, server):
        self.server = server
        self.up = 0
        self.down = 0
        self.up_speed = 0
        self.down_speed = 0
        self._last_up = 0
        self._last_down = 0
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def _monitor(self):
        while self._running:
            up = getattr(self.server, 'bytes_sent', 0)
            down = getattr(self.server, 'bytes_received', 0)
            self.up_speed = up - self._last_up
            self.down_speed = down - self._last_down
            self.up = up
            self.down = down
            self._last_up = up
            self._last_down = down
            time.sleep(1)

    def stop(self):
        self._running = False
