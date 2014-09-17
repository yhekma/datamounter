#!/usr/bin/env python

import sys
import cPickle
import stat
from fuse import FUSE, Operations

class AnsFS(Operations):
    def __init__(self, pklfile):
        f = open(pklfile, 'rb')
        self.struct = cPickle.load(f)
        f.close()
        self.fd = 0

    def getattr(self, path, fh=None):
        splitted_path = path.split('/')
        s = ''
        size = 1
        host = splitted_path[1]

        try:
            dir1 = splitted_path[2]
            dir2 = splitted_path[3] # NOQA
            s = stat.S_IFREG | 0444
            size = len(self.struct[host][dir1][dir2])
        except:
            try:
                dir1 = splitted_path[2]
                if type(self.struct[host][dir1]) == dict:
                    s = stat.S_IFDIR | 0555
                else:
                    s = stat.S_IFREG | 0444
                    size = len(self.struct[host][dir1])
            except:
                s = stat.S_IFDIR | 0555

        ret_dict = {'st_ctime': 1.1, 'st_mtime': 1.0, 'st_nlink': 1, 'st_mode': s, 'st_size': size, 'st_gid': 0, 'st_uid': 0, 'st_atime': 1.1}
        return ret_dict

    def readdir(self, path, fh):
        dirents = ['.', '..']
        splitted_path = path.split('/')

        if path == '/':
            dirents.extend(self.struct.keys())

        else:
            host = splitted_path[1]

            try:
                dir1 = splitted_path[2]
                dir2 = splitted_path[3]
                dirents.extend(self.struct[host][dir1][dir2])
            except:
                try:
                    dir1 = splitted_path[2]
                    dirents.extend(self.struct[host][dir1])
                except:
                    dirents.extend(self.struct[host])

        # elif len(splitted_path) == 2:
        #     p = splitted_path[1]
        #     dirents.extend(self.struct[p].keys())

        for r in dirents:
            yield r

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, length, offset, fh):
#        os.lseek(fh, offset, os.SEEK_SET)
#        return os.read(fh, length)
        splitted_path = path.split('/')
        host = splitted_path[1]
        item = splitted_path[2]
        value = self.struct[host][item]
        return str(value)


def main(pkl, mountpoint):
    FUSE(AnsFS(pkl), mountpoint, foreground=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
