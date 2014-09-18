#!/usr/bin/env python

import sys
import stat
import ansible.runner
from fuse import FUSE, Operations

class AnsFS(Operations):
    def __init__(self, pattern):
        self.struct = self._load_struct(pattern)
        self.fd = 0

    def _load_struct(self, pattern):
        runner = ansible.runner.Runner(
                module_name="setup",
                module_args="",
                forks=10,
                pattern=pattern,
            )
        tempstruct = runner.run()
        struct = {}
        for host in tempstruct['contacted']:
            struct[host] = tempstruct['contacted'][host]['ansible_facts']

        try:
            for host in struct.keys():
                for item in struct[host].keys():
                    if item.startswith('ansible_eth'):
                        for ip_val in struct[host][item]['ipv4'].keys():
                            struct[host][item][ip_val] = struct[host][item]['ipv4'][ip_val]
                        struct[host][item].pop('ipv4')
        except KeyError:
            pass

        print "Loaded"
        return struct

    def _split_path(self, path):
        splitted_path = path.split('/')
        while '' in splitted_path:
            splitted_path.remove('')

        return splitted_path

    def getattr(self, path, fh=None):
        splitted_path = self._split_path(path)
        s = stat.S_IFREG | 0444
        val = ''

        try:
            host = splitted_path[0]
        except:
            host = ''
            s = stat.S_IFDIR | 0555

        if len(splitted_path) <= 1:
            s = stat.S_IFDIR | 0555
        elif len(splitted_path) == 2:
            try:
                val = self.struct[host][splitted_path[1]]
            except:
                val = ''
            if type(val) == dict:
                s = stat.S_IFDIR | 0555
            else:
                s = stat.S_IFREG | 0444
        elif len(splitted_path) == 3:
            val = self.struct[host][splitted_path[1]][splitted_path[2]]
            if type(val) == dict:
                s = stat.S_IFDIR | 0555
            else:
                s = stat.S_IFREG | 0444

        size = len(str(val)) + 1
        return {'st_ctime': 1.1, 'st_mtime': 1.0, 'st_nlink': 1, 'st_mode': s, 'st_size': size, 'st_gid': 0, 'st_uid': 0, 'st_atime': 1.1}

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
        try:
            item2 = splitted_path[2]
            x = "%s\n" % str(self.struct[host][item][item2])
            return x
        except IndexError:
            x = "%s\n" % str(self.struct[host][item])
            return x

def main(pkl, mountpoint):
    FUSE(AnsFS(pkl), mountpoint, foreground=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
