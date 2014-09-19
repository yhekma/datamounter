#!/usr/bin/env python

import stat
import ansible.runner
import cPickle
import argparse
from fuse import FUSE, Operations

def fetch_struct(pattern):
    runner = ansible.runner.Runner(
            module_name="setup",
            module_args="",
            forks=10,
            pattern=pattern,
        )
    struct = runner.run()
    print "Loaded"

    return struct

def load_struct(pklfile):
    f = open(pklfile, 'rb')
    struct = cPickle.load(f)
    f.close()
    return struct

def save_struct(pklfile, struct):
    f = open(pklfile, 'wb')
    cPickle.dump(struct, f)
    f.close()

def flatten_struct(struct):
    tempstruct = struct.copy()
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

    return struct

def create_struct(args):
    struct = {}
    if args.cache:
        tempstruct = load_struct(args.cache)
        return flatten_struct(tempstruct)

    if args.gencache:
        tempstruct = fetch_struct(args.pattern)
        save_struct(args.gencache, tempstruct)
        struct = flatten_struct(tempstruct)
        return struct

    if args.pattern:
        tempstruct = fetch_struct(args.pattern)
        return flatten_struct(tempstruct)


class AnsFS(Operations):
    def __init__(self, struct):
        self.struct = struct
        self.fd = 0

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
    FUSE(AnsFS(struct), mountpoint, foreground=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mount virtual ansible-based filesystem using Fuse")
    parser.add_argument("--gen-cache", "-g", dest="gencache", default=False, help="Write a cache file at this location and exit")
    parser.add_argument("--cache", "-c", dest="cache", default=False, help="Location of the cache-file if wanted")
    parser.add_argument("--pattern", "-p", dest="pattern", default=False,
            help="Pattern to extract info from. Needed when generating a cache file and when not using a cache file")
    parser.add_argument("--mountpoint", "-m", dest="mountpoint", help="Where to mount the filesystem")
    args = parser.parse_args()
    struct = create_struct(args)
    main(struct, args.mountpoint)
