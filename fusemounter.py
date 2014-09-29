#!/usr/bin/env python

import sys
import argparse
from lib.ansfuse import AnsFS, create_struct
from fuse import FUSE


def main(pkl, mountpoint, realtime, f):
    FUSE(AnsFS(struct, realtime), mountpoint, foreground=f)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print 'Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0]
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual ansible-based filesystem using Fuse")
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument("mountpoint", help="Where to mount the filesystem", nargs="+")
    parser.add_argument("--gen-cache", "-g", dest="gencache", default=False, help="Write a cache file at this location and exit")
    group.add_argument("--cache", "-c", dest="cache", default=False, help="Location of the cache-file if wanted")
    group.add_argument("--pattern", "-p", dest="pattern", default=False,
            help="Pattern to extract info from. Needed when generating a cache file and when not using a cache file")
    parser.add_argument("--realtime", "-t", action="store_true", default=False, dest='realtime',
            help="Get the values real-time. Experimental")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground", help="Run in foreground")
    parser.add_argument("--retries", "-r", dest="retries", default=0, required=False, help="Optional number of retries to contact unreachable hosts")
    args = parser.parse_args()
    print "Loading data"
    struct = create_struct(args)
    print "done"
    main(struct, args.mountpoint[0], args.realtime, args.foreground)