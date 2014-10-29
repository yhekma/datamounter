import ansible.runner
import cPickle
import time
import stat
from fuse import Operations

def run_custom_command(pattern, command):
    runner = ansible.runner.Runner(
            module_name="shell",
            module_args=command,
            pattern=pattern,
        )
    return runner.run()

class AnsFS(Operations):
    def __init__(self, struct, realtime=False):
        self.epoch_time = time.time()
        self.realtime = realtime
        self.struct = struct
        self.fd = 0
        self.ctimedict = {}
        self.atimes = {}

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
        try:
            ctime = self.ctimedict[str(path)]
        except KeyError:
            ctime = self.epoch_time

        return {'st_ctime': self.epoch_time, 'st_mtime': ctime, 'st_nlink': 1, 'st_mode': s, 'st_size': size, 'st_gid': 0, 'st_uid': 0, 'st_atime': 1.1}

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
        x = ''
        realtime = False
    
        if self.realtime: # Do we want to do realtime?
            try:
                if time.time() - int(self.atimes[str(path)]) > 3: # If item was accessed more than 3 seconds ago
                    realtime = True
                    self.atimes[str(path)] = time.time() # Update access times
            except KeyError: # First time we access this file
                realtime = True
                self.atimes[str(path)] = time.time()

        try:
            item2 = splitted_path[2]
            if realtime and item2 in self.struct[host][item].keys():
                x = str(self._get_real_data(host)[host][item][item2])
                self.ctimedict[str(path)] = time.time()
            else:
                try:
                    x = "%s\n" % str(self.struct[host][item][item2])
                except KeyError:
                    pass

        except IndexError:
            if realtime and item in self.struct[host].keys():
                x = str(self._get_real_data(host)[host][item])
                self.ctimedict[str(path)] = time.time()
            else:
                try:
                    x = "%s\n" % str(self.struct[host][item])
                except KeyError:
                    pass
        return x

def create_struct(args, pattern=None, command=None):
    if args.cache:
        struct = load_struct(args.cache)
        if pattern:
            custom_commands = run_custom_command(pattern, command)
        else:
            custom_commands = None

        return flatten_struct(struct, custom_commands)

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
                try:
                    struct['dark'].pop(host)
                except KeyError:
                    pass
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

def flatten_struct(struct, custom_output=None):
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

    if custom_output:
        for filename in custom_output.keys():
            for host in custom_output[filename]['contacted'].keys():
                output = custom_output[filename]['contacted'][host]['stdout']
                newstruct[host][filename] = output

    return newstruct
