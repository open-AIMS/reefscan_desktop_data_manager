import re
import time
from threading import Thread

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from ping3 import ping

from aims.state import state
from fabric import Connection


class PingThread(QObject):
    ready = QtCore.pyqtSignal(bool)
    # success flag

    def __init__(self):
        super().__init__()
        self.thread = None
        self.cancelled = False
        self.running = True
        self.delayed_start = False

    def ping_task(self):
        self.running = True
        if state.config.v2:
            ping_ip = "192.168.144.1"
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
                try:
                    camera_ip  = self.get_v2_camera_ip()
                except:
                    camera_ip = None
                if not self.cancelled:
                    state.config.camera_ip = camera_ip
                    state.config.hardware_data_folder = f"\\\\{camera_ip}\images"
                    state.config.username = "reefscan"
                    print(f"updated camera_ip to {camera_ip}")
                    if camera_ip:
                        self.ready.emit(True)
                    else :
                        self.ready.emit(False)
            else:
                self.ready.emit(True)

        print("finished ping")

    def get_v2_camera_ip(self):
        """
        we can get the ip of the camera_box by looking at the lease file on the control box
        so ssh to the camera box
        """

        if self.delayed_start:
            time.sleep(1)

        conn = Connection(
            "reefscan" + "@" + "192.168.144.1",
            connect_kwargs={"password": ("%s" % "reefscan")}
        )

        leases = conn.run("bash /usr/local/bin/list-pi-network-clients.sh", hide=True).stdout.strip()
        # leases will be string that looks like this.
        """
IP Address      Hostname                  MAC Address        mDNS (.local)
--------------- ------------------------  ------------------ -------------------------
192.168.144.129 (n/a)                     52:e1:bb:01:42:c3  (n/a)
192.168.144.128 reefscan-camera-a44efb    88:a2:9e:04:ba:35  (n/a)
192.168.144.143 (n/a)                     34:73:5a:f3:40:13  (n/a)        
        """
        # parse that string to find the first IP Address that has "camera" in the Hostname

        print (leases)

        lines = leases.strip().splitlines()

        print (f"lines: {len(lines)}")

        # Skip header lines (first two lines)
        data_lines = lines[2:]

        for line in data_lines:
            # Skip empty or separator lines
            if not line.strip() or set(line.strip()) == {"-"}:
                continue

            # Split using any whitespace groups
            parts = re.split(r"\s+", line.strip())

            # Expect at least: IP, Hostname, MAC
            if len(parts) < 3:
                continue

            ip = parts[0]
            hostname = parts[1]

            print(ip, hostname)

            if "camera" in hostname.lower():
                return ip

        return None




    def start(self, delayed_start=False):
        print("start")
        self.cancelled = False
        self.delayed_start = delayed_start
        thread = Thread(target=self.ping_task)
        # daemon threads will stop when the main thread stops
        thread.daemon = True
        thread.start()

    def cancel(self):
        print("cancelled")
        self.cancelled = True