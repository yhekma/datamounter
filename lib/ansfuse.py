import ansible.runner
import cPickle
import time
import stat
import os
import pwd
from fuse import Operations

uid = pwd.getpwuid(os.getuid()).pw_uid
gid = pwd.getpwuid(os.getuid()).pw_gid

def recursive_lookup(path, struct):
    if not type(struct) == dict:
        return struct
    if len(path) == 0:
        return struct

    newpath = path[1:]
    return recursive_lookup(newpath, struct[path[0]])

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
        val = recursive_lookup(splitted_path, self.struct)

        if type(val) == dict:
            s = stat.S_IFDIR | 0555
        else:
            s = stat.S_IFREG | 0444

        size = len(str(val)) + 1

        try:
            ctime = self.ctimedict[str(path)]
        except KeyError:
            ctime = self.epoch_time

        return {'st_ctime': self.epoch_time, 'st_mtime': ctime, 'st_mode': s, 'st_size': size, 'st_gid': gid, 'st_uid': uid, 'st_atime': 1.1}

    def readdir(self, path, fh):
        dirents = ['.', '..']
        splitted_path = self._split_path(path)
        path_tip = recursive_lookup(splitted_path, self.struct)

        if len(splitted_path) == 0:
            dirents.extend(self.struct.keys())
            for r in dirents:
                yield r

        else:
            dirents.extend(path_tip.keys())
            for r in dirents:
                yield r

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, length, offset, fh):
        splitted_path = self._split_path(path)

        if self.realtime:
            host = splitted_path[0]

            try:
                if int(time.time()-self.atimes[path]) < 10:
                    self.atimes[path] = time.time()
                else:
                    current_host_data = self._get_real_data(host)
                    self.struct[host] = current_host_data[host]
                    self.atimes[path] = time.time()

            except KeyError:
                current_host_data = self._get_real_data(host)
                self.struct[host] = current_host_data[host]
                self.atimes[path] = time.time()


        path_tip = recursive_lookup(splitted_path, self.struct)
    
        return "%s\n" % str(path_tip)

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
                newstruct[host]['mounts'][diskname] = mount
            except KeyError:
                newstruct[host]['mounts'] = {diskname: mount}

        newstruct[host].pop('ansible_mounts')

    if custom_output:
        for filename in custom_output.keys():
            for host in custom_output[filename]['contacted'].keys():
                output = custom_output[filename]['contacted'][host]['stdout']
                newstruct[host][filename] = output

    return newstruct
