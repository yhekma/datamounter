Datamounter
=======

FUSE filesystem populated from JSON. Optionally from ansible's setup module

Usage
-----
```
usage: datamounter.py [-h] [--gen-cache GENCACHE]
                      (--cache CACHE | --pattern PATTERN) [--foreground]
                      [--retries RETRIES] [--custom CUSTOM] [--realtime]
                      [--allow_other]
                      mountpoint [mountpoint ...]

Mount virtual filesystem using json/ansible as input

positional arguments:
  mountpoint            Where to mount the filesystem

optional arguments:
  -h, --help            show this help message and exit
  --gen-cache GENCACHE, -g GENCACHE
                        Write a cache file at this location
  --cache CACHE, -c CACHE
                        Location of the cache-file if wanted
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --foreground, -f      Run in foreground
  --retries RETRIES, -r RETRIES
                        Optional number of retries to contact unreachable
                        hosts
  --custom CUSTOM       Optional ini file with custom commands to run on
                        remote host which output to expose. Files will show up
                        under custom_facts/.
  --realtime            Fetch data realtime. Experimental.
  --allow_other, -a     Allow other users to read from the filesystem.
```

Example Usage
-----
Map the pre-generated datafile stored in **dev.json** on **/opt/infra_map**:

```datamounter.py -c dev.json /opt/infra_map```


Map the hosts defined in the **prod** group as defined in [ansible inventory] to **/opt/prod_map** and update the values in realtime:

```datamounter.py -p prod --realtime /opt/prod_map```


Scan the **production-env** (as defined in your [ansible inventory]), save it in **prod.json** and map in on **/opt/infra/prod**:

```datamounter.py -g prod.json -p production-env -m /opt/infra_prod```

[Ansible]:http://www.ansible.com/
[ansible inventory]:http://docs.ansible.com/intro_inventory.html
