import time
from threading import Thread

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from ping3 import ping

from aims.state import state


class PingThread(QObject):
    ready = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.cancelled = False
        self.running = True

    def ping_task(self):
        self.running = True
        print("task")
        r = None
        while r is None and not self.cancelled:
            r = ping(state.config.camera_ip, timeout=1)
            print(r)

        self.running = False
        if not self.cancelled:
            self.ready.emit(1)
        print("finished ping")

    def start(self):
        print("start")
        self.cancelled = False
        thread = Thread(target=self.ping_task)
        # daemon threads will stop when the main thread stops
        thread.daemon = True
        thread.start()

    def cancel(self):
        self.cancelled = True