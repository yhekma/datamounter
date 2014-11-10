#!/usr/bin/env python

import sys
import argparse
import ConfigParser
from lib.ansfuse import AnsFS, load_struct, run_custom_command, flatten_struct, save_struct, fetch_struct
from fuse import FUSE

def load_ini(path):
    config = ConfigParser.RawConfigParser()
    config.read(path)
    result = {}
    for host in config.sections():
        for item in config.items(host):
            try:
                result[host][item[0]] = item[1]
            except KeyError:
                result[host] = {item[0]: item[1]}

    return result


def main(pkl, mountpoint, f, realtime):
    FUSE(AnsFS(struct, realtime), mountpoint, foreground=f)

if __name__ == "__main__":
    struct = {}
    if len(sys.argv) == 1:
        print 'Please specify what to mount where. Use "%s -h" for help.' % sys.argv[0]
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Mount virtual ansible-based filesystem using Fuse")
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument("mountpoint", help="Where to mount the filesystem", nargs="+")
    parser.add_argument("--gen-cache", "-g", dest="gencache", default=False, help="Write a cache file at this location")
    group.add_argument("--cache", "-c", dest="cache", default=False, help="Location of the cache-file if wanted")
    group.add_argument("--pattern", "-p", dest="pattern", default=False,
            help="Pattern to extract info from. Needed when generating a cache file and when not using a cache file")
    parser.add_argument("--foreground", "-f", action="store_true", default=False, dest="foreground", help="Run in foreground")
    parser.add_argument("--retries", "-r", dest="retries", default=0, required=False, help="Optional number of retries to contact unreachable hosts")
    parser.add_argument("--custom", required=False, help="Optional ini file with custom commands to run on remote host which output to expose", default=None)
    parser.add_argument("--realtime", action="store_true", required=False, help="Fetch data realtime. Experimental.", dest="realtime", default=False)
    args = parser.parse_args()
    print "Loading data"

    if args.custom:
        cust = load_ini(args.custom)
        custom_commands = {}
        for host in cust.keys():
            for filename in cust[host].keys():
                custom_commands[filename] = run_custom_command(host, cust[host][filename])

    else:
        custom_commands = None

    if args.cache:
        struct = load_struct(args.cache)
        struct = flatten_struct(struct, custom_commands)

    elif args.gencache:
        tempstruct = fetch_struct(args.pattern, args.retries)
        struct = flatten_struct(tempstruct, custom_commands)
        save_struct(args.gencache, tempstruct)

    elif args.pattern:
        tempstruct = fetch_struct(args.pattern, args.retries)
        struct = flatten_struct(tempstruct, custom_commands)

    print "done"
    main(struct, args.mountpoint[0], args.foreground, args.realtime)
