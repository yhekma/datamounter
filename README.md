Datamounter
=======

FUSE filesystem populated from JSON. Optionally from ansible's setup module

Components
-----
ansible_fetcher.py can be used to fetch information using Ansible's setup module
and optionally custom commands/facts. It outputs a slightly modified json file for
use with the datamounter.py script.

Usage ansible_fetcher.py
-----
```
usage: ansible_fetcher.py [-h] [--pattern PATTERN] [--retries RETRIES] -f
                          FILENAME [--custom CUSTOM]

Fetch information from remote systems using Ansible

optional arguments:
  -h, --help            show this help message and exit
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --retries RETRIES, -r RETRIES
                        Optional number of retries to contact unreachable
                        hosts
  -f FILENAME, --filename FILENAME
                        Destination filename for the json data.
  --custom CUSTOM       Optional ini file with custom commands to run on
                        remote host which output to expose. Files will show up
                        under custom_facts/.
```

Usage datamounter.py
-----
```
usage: datamounter.py [-h] --cache CACHE [--foreground] [--realtime]
                      [--allow_other]
                      mountpoint [mountpoint ...]

Mount virtual filesystem using json/ansible as input

positional arguments:
  mountpoint            Where to mount the filesystem

optional arguments:
  -h, --help            show this help message and exit
  --cache CACHE, -c CACHE
                        Location of the cache-file if wanted
  --foreground, -f      Run in foreground
  --realtime            Fetch data realtime. Experimental.
  --allow_other, -a     Allow other users to read from the filesystem.
```

Example Usage
-----
Map the pre-generated datafile stored in **dev.json** on **/opt/infra_map**:

```datamounter.py -c dev.json /opt/infra_map```


Create a json file for all the **prod** hosts as defined in [ansible inventory] and save it to **prod.json**:

```ansible_fetcher.py -p prod -f prod.json```


Scan the **production-env** (as defined in your [ansible inventory]), save it in **prod.json** and map in on **/opt/infra/prod**:
Mount a generated json file named **prod.json** on /opt/infra_prod:

```datamounter.py -c prod.json /opt/infra_prod```

[Ansible]:http://www.ansible.com/
[ansible inventory]:http://docs.ansible.com/intro_inventory.html
