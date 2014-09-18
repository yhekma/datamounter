#!/usr/bin/env python

import sys
import cPickle
import stat
from fuse import FUSE, Operations

class AnsFS(Operations):
    def __init__(self, pklfile):
        self.struct = self._load_struct(pklfile)
        self.fd = 0

    def _load_struct(self, filename):
        f = open(filename, 'rb')
        struct = cPickle.load(f)
        f.close()
        return struct

    def _flatten_struct(self, struct):
        pass

    def _split_path(self, path):
        splitted_path = path.split('/')
        while '' in splitted_path:
            splitted_path.remove('')

        return splitted_path

    def getattr(self, path, fh=None):
        splitted_path = self._split_path(path)
        s = ''
        size = 1

        try:
            host = splitted_path[0]
        except:
            host = ''
            s = stat.S_IFDIR | 0555

        if len(splitted_path) <= 1:
            s = stat.S_IFDIR | 0555
        else:
            val = self.struct[host][splitted_path[1]]
            if type(val) == dict:
                s = stat.S_IFDIR | 0555
            else:
                size = len(str(val))
                s = stat.S_IFREG | 0444

        ret_dict = {'st_ctime': 1.1, 'st_mtime': 1.0, 'st_nlink': 1, 'st_mode': s, 'st_size': size, 'st_gid': 0, 'st_uid': 0, 'st_atime': 1.1}
        return ret_dict

    def readdir(self, path, fh):
        dirents = ['.', '..']
        splitted_path = self._split_path(path)

        if len(splitted_path) == 0:
            dirents.extend(self.struct.keys())
            for r in dirents:
                yield r

        else:
            host = splitted_path[0]
            try:
                dirents.extend(self.struct[host][splitted_path[1]].keys())
            except IndexError:
                dirents.extend(self.struct[host].keys())
            for r in dirents:
                yield r

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, length, offset, fh):
        splitted_path = self._split_path(path)
        host = splitted_path[0]
        item = splitted_path[1]
        return str(self.struct[host][item][offset:offset+length])


def main(pkl, mountpoint):
    FUSE(AnsFS(pkl), mountpoint, foreground=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
