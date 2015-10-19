#!/usr/bin/env python

import sys

from dlib.datamounter_helpers import DataFS, load_struct
from dlib.ansible_helpers import gut_struct

try:
    import argparse
except ImportError:
    from local_libs import argparse_local as argparse
try:
    from fuse import FUSE
except ImportError:
    from local_libs.fuse_local import FUSE


def main(datastruct, mountpoint, f, realtime, allow_other, utime, clean):
    FUSE(DataFS(datastruct, realtime, utime, clean), mountpoint, allow_other=allow_other, foreground=f, ro=True)


if __name__ == "__main__":
    struct = {}
    if len(sys.argv) == 1:
        print 'Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0]
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual filesystem using json/ansible as input")
    parser.add_argument("mountpoint", help="Where to mount the filesystem", nargs="+")
    required = parser.add_argument_group('required arguments')
    required.add_argument("--cache", "-c", dest="cache", required=True, help="Location of the cache-file.")
    parser.add_argument("--updatetime", dest="utime", required=False, type=int, default=10,
                        help="""Optionally tell the mounter how long the contents of files will be cached after which
                        the fact is retrieved again. To be used with --realtime. Defaults to 10 seconds""")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground",
                        help="Run in foreground", required=False)
    parser.add_argument("--allow_other", "-a", action="store_true", required=False,
                        help="Allow other users to read from the filesystem.", dest="allow_other", default=False)
    parser.add_argument("--skeleton", "-s", action="store_true", required=False, default=False,
                        help="""Remove all values from the datastructure, essentially leaving only the structure itself.
                        Useful in combination with --realtime""")
    parser.add_argument("--realtime", action="store_true", required=False, help="Fetch data realtime.",
                        dest="realtime", default=False)
    parser.add_argument("--disable-cleanup", "-d", action="store_true", default=False, dest="disable_cleanup",
                        help="Disable the cleanup thread. Use only when you have trouble with threading.")

    args = parser.parse_args()
    print "Loading data"

    struct = load_struct(args.cache)

    if args.skeleton:
        gut_struct(struct)

    print "done"
    if args.realtime and not args.disable_cleanup:
        cleanup = True
    else:
        cleanup = False

    try:
        main(struct, args.mountpoint[0], args.foreground, args.realtime, args.allow_other, args.utime, cleanup)
    except KeyboardInterrupt:
        sys.exit()
