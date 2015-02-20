#!/usr/bin/env python

import argparse
import ConfigParser
from lib.ansible_helpers import flatten_ansible_struct, fetch_struct, run_custom_command, gut_struct, save_struct


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch information from remote systems using Ansible")
    parser.add_argument("--pattern", "-p", dest="pattern", default=False, required=True,
                        help="Pattern to extract info from. Needed when generating a cache file and when not using a cache file")
    parser.add_argument("--retries", "-r", dest="retries", default=3, required=False,
                        help="Optional number of retries to contact unreachable hosts")
    parser.add_argument("-f", "--filename", dest="filename", required=True,
                        help="Destination filename for the json data.")
    parser.add_argument("--custom", required=False,
                        help="Optional ini file with custom commands to run on remote host which output to expose. Files will show up under custom_facts/.",
                        default=None)
    parser.add_argument("--skeleton", "-s", action="store_true", required=False, default=False,
                        help="Remove all values from the datastructure, essentially leaving only the structure itself. Useful in combination with --realtime")
    args = parser.parse_args()

    if args.custom:
        cust_input = load_ini(args.custom)
        custom_commands = {}
        for host in cust_input.keys():
            for filename in cust_input[host].keys():
                custom_commands[filename] = run_custom_command(host, cust_input[host][filename], args.pattern,
                                                               args.skeleton)

    else:
        custom_commands = None

    tempstruct = fetch_struct(args.pattern, args.retries)
    struct = flatten_ansible_struct(tempstruct, custom_commands)
    if args.skeleton:
        gut_struct(struct)
    save_struct(args.filename, struct)
