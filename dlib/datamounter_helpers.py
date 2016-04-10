import json
import time
import stat
import os
import pwd
from fuse import Operations


uid = pwd.getpwuid(os.getuid()).pw_uid
gid = pwd.getpwuid(os.getuid()).pw_gid


class DataFS(Operations):
    def __init__(self, struct, utime=10):
        self.utime = utime
        self.epoch_time = time.time()
        self.struct = struct
        self.ctimedict = {}
        self.fetch_times = {}

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
            s = stat.S_IFDIR | 0o555
        else:
            s = stat.S_IFREG | 0o444

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
            dirents.extend(list(self.struct.keys()))
            for r in dirents:
                yield r

        else:
            dirents.extend(list(path_tip.keys()))
            for r in dirents:
                yield r

    def read(self, path, length, offset, fh):
        splitted_path = split_path(path)
        host = splitted_path[0]
        if host not in list(self.fetch_times.keys()):
            self.fetch_times[host] = 0

        path_tip = str(self._recursive_lookup(splitted_path, self.struct)) + "\n"
        r = path_tip[offset:offset + length]
        return r


def load_struct(pklfile):
    with open(pklfile, 'r') as handle:
        struct = json.loads(handle.read())
        return struct


def split_path(path):
    splitted_path = path.split('/')
    while '' in splitted_path:
        splitted_path.remove('')

    return splitted_path
