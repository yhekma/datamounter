#!/usr/bin/env python

import stat
import sys
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
    newstruct = {}
    tempstruct = {}
    for host in struct['contacted']:
        tempstruct[host] = struct['contacted'][host]['ansible_facts']

    # Remove ipv4 and put contents one "dir" higher
    for host in tempstruct.keys():
        for item in tempstruct[host].keys():
            if item.startswith('ansible_eth'):
                try:
                    newstruct[host][item] = tempstruct[host][item].pop('ipv4')
                except KeyError:
                    try:
                        newstruct[host] = {item: tempstruct[host][item].pop('ipv4')}
                    except KeyError:
                        pass
                for net_item in tempstruct[host][item]:
                    try:
                        newstruct[host][item][net_item] = tempstruct[host][item][net_item]
                    except KeyError:
                        newstruct[host][item] = {net_item: tempstruct[host][item][net_item]}
            else:
                try:
                    newstruct[host][item] = tempstruct[host][item]
                except KeyError:
                    newstruct[host] = {item: tempstruct[host][item]}

    # Walk through "ansible_mounts" (list) and create direntries
    for host in newstruct.keys():
        for mount in newstruct[host]['ansible_mounts']:
            diskname = mount['device'].split('/')[-1:][0]
            try:
                newstruct[host]['ansible_mount_devices'][diskname] = str(mount)
            except KeyError:
                newstruct[host]['ansible_mount_devices'] = {diskname: str(mount)}

        newstruct[host].pop('ansible_mounts')

    return newstruct

def create_struct(args):
    if args.cache:
        struct = load_struct(args.cache)
        return flatten_struct(struct)

    if args.gencache:
        tempstruct = fetch_struct(args.pattern)
        struct = flatten_struct(tempstruct)
        save_struct(args.gencache, struct)
        return struct

    if args.pattern:
        tempstruct = fetch_struct(args.pattern)
        return flatten_struct(tempstruct)


class AnsFS(Operations):
    def __init__(self, struct, realtime=False):
        self.realtime = realtime
        self.struct = struct
        self.fd = 0

    def _split_path(self, path):
        splitted_path = path.split('/')
        while '' in splitted_path:
            splitted_path.remove('')

        return splitted_path

    def _get_real_data(self, host):
        runner = ansible.runner.Runner(
                module_name="setup",
                module_args="",
                forks=1,
                pattern=host,
            )
        data = runner.run()
        try:
            return flatten_struct(data)
        except KeyError:
            pass

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
            if self.realtime:
                x = str(self._get_real_data(host)[host][item][item2])
            else:
                x = "%s\n" % str(self.struct[host][item][item2])
            return x
        except IndexError:
            if self.realtime:
                x = str(self._get_real_data(host)[host][item])
            else:
                x = "%s\n" % str(self.struct[host][item])
            return x


def main(pkl, mountpoint, realtime, f):
    FUSE(AnsFS(struct, realtime), mountpoint, foreground=f)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print 'Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0]
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual ansible-based filesystem using Fuse")
    parser.add_argument("--gen-cache", "-g", dest="gencache", default=False, help="Write a cache file at this location and exit")
    parser.add_argument("--cache", "-c", dest="cache", default=False, help="Location of the cache-file if wanted")
    parser.add_argument("--pattern", "-p", dest="pattern", default=False,
            help="Pattern to extract info from. Needed when generating a cache file and when not using a cache file")
    parser.add_argument("--mountpoint", "-m", dest="mountpoint", help="Where to mount the filesystem")
    parser.add_argument("--realtime", "-t", action="store_true", default=False, dest='realtime',
            help="Get the values real-time. Experimental")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground", help="Run in foreground")
    args = parser.parse_args()
    print "Loading data"
    struct = create_struct(args)
    print "done"
    main(struct, args.mountpoint, args.realtime, args.foreground)
