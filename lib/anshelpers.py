import ansible.runner
import cPickle

def create_struct(args):
    if args.cache:
        struct = load_struct(args.cache)
        return flatten_struct(struct)

    if args.gencache:
        tempstruct = fetch_struct(args.pattern, args.retries)
        struct = flatten_struct(tempstruct)
        save_struct(args.gencache, tempstruct)
        return struct

    if args.pattern:
        tempstruct = fetch_struct(args.pattern, args.retries)
        return flatten_struct(tempstruct)


def gen_runner(pattern):
    runner = ansible.runner.Runner(
            module_name="setup",
            module_args="",
            forks=10,
            pattern=pattern,
        )

    return runner

def fetch_struct(pattern, retries=0):
    runner = gen_runner(pattern)
    struct = runner.run()

    for r in range(int(retries)):
        if not len(struct['dark']) == 0:
            newpattern = ':'.join(struct['dark'].keys())
            print "Retrying %s" % newpattern
            newrunner = gen_runner(newpattern)
            newstruct = newrunner.run()
            for host in newstruct['contacted'].keys():
                struct['contacted'][host] = newstruct['contacted'][host]

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

    # Move everything in "ansible_local" one level up
    for host in newstruct.keys():
        try:
            for fact in newstruct[host]['ansible_local'].keys():
                newstruct[host][fact] = newstruct[host]['ansible_local'][fact]
        except KeyError:
            pass
        newstruct[host].pop('ansible_local')

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
