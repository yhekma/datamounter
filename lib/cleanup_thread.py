import threading
from time import sleep
from ansible_helpers import gut_struct

class cleanup_thread(threading.Thread):
    def __init__(self, sleeptime, struct, lock):
        threading.Thread.__init__(self)
        self.sleeptime = sleeptime
        self.struct = struct
        self.daemon = True
        self.lock = lock

    def run(self):
        while True:
            self.lock.acquire()
            gut_struct(self.struct)
            self.lock.release()
            sleep(self.sleeptime)
