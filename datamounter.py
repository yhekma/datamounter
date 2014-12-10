#!/usr/bin/env python

import sys
import argparse
from lib.datamounter import DataFS, load_struct
from fuse import FUSE

def main(pkl, mountpoint, f, realtime, allow_other=False):
    FUSE(DataFS(struct, realtime), mountpoint, allow_other=allow_other, foreground=f, ro=True)

if __name__ == "__main__":
    struct = {}
    if len(sys.argv) == 1:
        print 'Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0]
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual filesystem using json/ansible as input")
    parser.add_argument("mountpoint", help="Where to mount the filesystem", nargs="+")
    parser.add_argument("--cache", "-c", dest="cache", required=True, help="Location of the cache-file if wanted")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground", help="Run in foreground")
    parser.add_argument("--realtime", action="store_true", required=False, help="Fetch data realtime. Experimental.", dest="realtime", default=False)
    parser.add_argument("--allow_other", "-a", action="store_true", required=False, help="Allow other users to read from the filesystem.", dest="allow_other", default=False)
    args = parser.parse_args()
    print "Loading data"

    struct = load_struct(args.cache)

    print "done"
    main(struct, args.mountpoint[0], args.foreground, args.realtime, args.allow_other)
