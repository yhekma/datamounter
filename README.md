AnsFUSE
=======

FUSE filesystem populated using the setup module from [Ansible].

Usage
-----
```ansfuse.py [-h] [--gen-cache GENCACHE] [--cache CACHE]
                  [--pattern PATTERN] [--mountpoint MOUNTPOINT] [--realtime]

optional arguments:
  -h, --help            show this help message and exit
  --gen-cache GENCACHE, -g GENCACHE
                        Write a cache file at this location and exit
  --cache CACHE, -c CACHE
                        Location of the cache-file if wanted
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --mountpoint MOUNTPOINT, -m MOUNTPOINT
                        Where to mount the filesystem
  --realtime, -t        Get the values real-time. Experimental

usage: ansfuse.py [-h] [--gen-cache GENCACHE] [--cache CACHE]
                  [--pattern PATTERN] [--mountpoint MOUNTPOINT] [--realtime]

```

Example Usage
-----
```ansfuse.py -c dev.pkl -m /opt/infra_map```
Map the pre-generated datafile stored in *dev.pkl* on */opt/infra_map*
```ansfuse.py -g prod.pkl -p production-env -m /opt/infra_prod```
Scan the *production-env* (as defined in your [ansible inventory], save it in *prod.pkl* and map in on */opt/infra/prod*


[Ansible]:http://www.ansible.com/
[ansible inventory]:http://docs.ansible.com/intro_inventory.html
