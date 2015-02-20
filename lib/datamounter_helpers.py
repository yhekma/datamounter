import json
import time
import stat
import os
import pwd
from ansible_helpers import get_real_data, run_custom_command
from fuse import Operations

uid = pwd.getpwuid(os.getuid()).pw_uid
gid = pwd.getpwuid(os.getuid()).pw_gid


class DataFS(Operations):
    def __init__(self, struct, realtime=False, utime=10, cleanup=False):
        self.cleanup = cleanup
        self.utime = utime
        self.epoch_time = time.time()
        self.realtime = realtime
        self.struct = struct
        self.ctimedict = {}
        self.fetch_times = {}
        if cleanup:
            import threading
            from cleanup_thread import cleanup_thread

            self.lock = threading.Lock()
            ct = cleanup_thread(3, self.struct, self.lock)
            ct.run()

    def _recursive_lookup(self, path, struct):
        if type(struct) == list:
            newdict = {}
            for index, i in enumerate(struct):
                filename = 'listitem_%s' % index
                newdict[filename] = i
            struct = newdict

        if len(path) == 0:
            return struct

        if not type(struct) == dict:
            return struct

        try:
            newpath = path[1:]
            return self._recursive_lookup(newpath, struct[path[0]])
        except KeyError:
            return None

    def getattr(self, path, fh=None):
        splitted_path = split_path(path)
        val = self._recursive_lookup(splitted_path, self.struct)

        if type(val) == dict:
            s = stat.S_IFDIR | 0555
        else:
            s = stat.S_IFREG | 0444

        size = len(str(val)) + 1

        try:
            ctime = self.ctimedict[str(path)]
        except KeyError:
            ctime = self.epoch_time

        return {'st_ctime': self.epoch_time, 'st_mtime': ctime, 'st_mode': s, 'st_size': size, 'st_gid': gid,
                'st_uid': uid, 'st_atime': 1.1}

    def readdir(self, path, fh):
        dirents = ['.', '..']
        splitted_path = split_path(path)
        path_tip = self._recursive_lookup(splitted_path, self.struct)

        if len(splitted_path) == 0:
            dirents.extend(self.struct.keys())
            for r in dirents:
                yield r

        else:
            dirents.extend(path_tip.keys())
            for r in dirents:
                yield r

    def read(self, path, length, offset, fh):
        splitted_path = split_path(path)
        host = splitted_path[0]
        if host not in self.fetch_times.keys():
            self.fetch_times[host] = 0

        if self.realtime:
            if self.cleanup:
                self.lock.acquire()

            if "custom_commands" not in splitted_path:
                try:
                    old_custom_commands = self.struct[host]['custom_commands']
                except KeyError:
                    old_custom_commands = None

                if int(time.time() - self.fetch_times[host]) < self.utime:
                    pass

                else:
                    if host in self.struct.keys():
                        current_host_data = get_real_data(host, old_custom_commands)
                        self.struct[host] = current_host_data[host]
                        self.fetch_times[host] = time.time()

            elif 'stdout' in splitted_path:
                if self.cleanup:
                    self.lock.acquire()

                if int(time.time() - self.fetch_times[host]) < self.utime:
                    pass
                else:
                    splitted_cmd_path = splitted_path[:splitted_path.index('custom_commands') + 2]
                    filename = splitted_cmd_path[-1:][0]
                    splitted_cmd_path.append('cmd')
                    cmd = str(self._recursive_lookup(splitted_cmd_path, self.struct)) + "\n"
                    output = {host: run_custom_command(host, cmd)}[host]['contacted']
                    self.struct[host]['custom_commands'][filename] = output[host]
                    self.fetch_times[host] = time.time()

        if self.cleanup:
            self.lock.release()

        path_tip = str(self._recursive_lookup(splitted_path, self.struct)) + "\n"
        r = path_tip[offset:offset + length]
        return r


def load_struct(pklfile):
    f = open(pklfile, 'rb')
    struct = json.load(f)
    f.close()
    return struct


def save_struct(pklfile, struct):
    f = open(pklfile, 'wb')
    json.dump(struct, f)
    f.close()


def split_path(path):
    splitted_path = path.split('/')
    while '' in splitted_path:
        splitted_path.remove('')

    return splitted_path
