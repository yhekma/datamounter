import threading
from time import sleep
from ansible_helpers import gut_struct

class cleanup_thread(threading.Thread):
    def __init__(self, sleeptime, struct):
        threading.Thread.__init__(self)
        self.sleeptime = sleeptime
        self.struct = struct
        self.daemon = True

    def run(self):
        while True:
            gut_struct(self.struct)
            sleep(self.sleeptime)
