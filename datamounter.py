#!/usr/bin/env python3

import sys

from dlib.datamounter_helpers import DataFS, load_struct

import argparse
from fuse import FUSE


def main(datastruct, mountpoint, f, allow_other):
    FUSE(DataFS(datastruct), mountpoint, allow_other=allow_other, foreground=f, ro=True)


if __name__ == "__main__":
    struct = {}
    if len(sys.argv) == 1:
        print('Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0])
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual filesystem using json/ansible as input")
    parser.add_argument("mountpoint", help="Where to mount the filesystem", nargs="+")
    required = parser.add_argument_group('required arguments')
    required.add_argument("--cache", "-c", dest="cache", required=True, help="Location of the cache-file.")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground",
                        help="Run in foreground", required=False)
    parser.add_argument("--allow_other", "-a", action="store_true", required=False,
                        help="Allow other users to read from the filesystem.", dest="allow_other", default=False)

    args = parser.parse_args()
    print("Loading data")

    struct = load_struct(args.cache)

    print("done")

    try:
        main(struct, args.mountpoint[0], args.foreground, args.allow_other)
    except KeyboardInterrupt:
        sys.exit()
