import cPickle
import time
import stat
import os
import pwd
from ansible_helpers import get_real_data
from fuse import Operations

uid = pwd.getpwuid(os.getuid()).pw_uid
gid = pwd.getpwuid(os.getuid()).pw_gid

class AnsFS(Operations):
    def __init__(self, struct, realtime=False):
        self.epoch_time = time.time()
        self.realtime = realtime
        self.struct = struct
        self.fd = 0
        self.ctimedict = {}
        self.fetch_times = {}

    def _split_path(self, path):
        splitted_path = path.split('/')
        while '' in splitted_path:
            splitted_path.remove('')

        return splitted_path

    def _recursive_lookup(self, path, struct):
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
        splitted_path = self._split_path(path)
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

        return {'st_ctime': self.epoch_time, 'st_mtime': ctime, 'st_mode': s, 'st_size': size, 'st_gid': gid, 'st_uid': uid, 'st_atime': 1.1}

    def readdir(self, path, fh):
        dirents = ['.', '..']
        splitted_path = self._split_path(path)
        path_tip = self._recursive_lookup(splitted_path, self.struct)

        if len(splitted_path) == 0:
            dirents.extend(self.struct.keys())
            for r in dirents:
                yield r

        else:
            dirents.extend(path_tip.keys())
            for r in dirents:
                yield r

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, length, offset, fh):
        splitted_path = self._split_path(path)

        if self.realtime and not "custom_commands" in splitted_path:
            host = splitted_path[0]

            try:
                if int(time.time() - self.fetch_times[host]) < 10:
                    pass

                else:
                    current_host_data = get_real_data(host)
                    self.struct[host] = current_host_data[host]
                    self.fetch_times[host] = time.time()

            except KeyError:
                current_host_data = get_real_data(host)
                self.struct[host] = current_host_data[host]
                self.fetch_times[host] = time.time()

        path_tip = self._recursive_lookup(splitted_path, self.struct)
        return "%s\n" % str(path_tip)

def load_struct(pklfile):
    f = open(pklfile, 'rb')
    struct = cPickle.load(f)
    f.close()
    return struct

def save_struct(pklfile, struct):
    f = open(pklfile, 'wb')
    cPickle.dump(struct, f)
    f.close()
