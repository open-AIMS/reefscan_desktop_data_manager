import time
from threading import Thread

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from ping3 import ping

from aims.state import state
from fabric import Connection


class PingThread(QObject):
    ready = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.cancelled = False
        self.running = True

    def ping_task(self):
        self.running = True
        if state.config.v2:
            ping_ip = "192.168.3.10"
        else:
            ping_ip = state.config.camera_ip

        print("task")
        r = None
        while r is None and not self.cancelled:
            try:
                r = ping(ping_ip, timeout=1)
            except:
                r = None
            print(r)

        self.running = False
        if not self.cancelled:
            if state.config.v2:
                camera_ip  = self.get_v2_camera_ip()
                state.config.camera_ip = camera_ip
                state.config.hardware_data_folder = f"\\{camera_ip}\images"
                state.config.username = "reefscan"
                print(f"updated camera_ip to {camera_ip}")
            self.ready.emit(1)
        print("finished ping")

    def get_v2_camera_ip(self):
        """
        we can get the ip of the camera_box by looking at the lease file on the control box
        so ssh to the camera box
        """

        conn = Connection(
            "reefscan" + "@" + "192.168.144.254",
            connect_kwargs={"password": ("%s" % "reefscan")}
        )
        return conn.run("awk '$4 ~ /reefscan/ {print $3}' /var/lib/misc/dnsmasq.leases", hide=True).stdout.strip()


    def start(self):
        print("start")
        self.cancelled = False
        thread = Thread(target=self.ping_task)
        # daemon threads will stop when the main thread stops
        thread.daemon = True
        thread.start()

    def cancel(self):
        print("cancelled")
        self.cancelled = True