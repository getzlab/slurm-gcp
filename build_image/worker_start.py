#!/usr/bin/python3
"""
Prepares all nodes and startup scripts
"""

import shlex
import time
import re
import subprocess
import os
import io
import socket
import json
import requests
import pandas as pd

def read_meta_key(key):
    response = requests.get(
        'http://metadata.google.internal/computeMetadata/v1/{key}'.format(key=key),
        headers={
            'Metadata-Flavor': 'Google'
        }
    )
    if response.status_code == 200:
        return response.text
    raise ValueError('({}) : {}'.format(response.status_code, response.text))

def main():
    instance_name = read_meta_key('instance/name')
    cluster = read_meta_key('instance/attributes/canine_conf_cluster_name')
    controller = read_meta_key('instance/attributes/canine_conf_controller')
    sec = read_meta_key('instance/attributes/canine_conf_sec')
    print("Starting worker", instance_name, "as part of cluster", cluster)
    print("Mounting NFS volumes")
    with open('/etc/fstab', 'a') as w:
        w.write('{controller}:/apps\t/apps\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        w.write('{controller}:/etc/munge\t/etc/munge\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        w.write('{controller}:/home\t/home\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        if len(sec) and sec != '-':
            w.write('{controller}:{sec}\t{sec}\tnfs\trw,hard,intr\t0\t0\n'.format(controller, sec))
    subprocess.check_call('rm -rf /home/*', shell=True)
    subprocess.check_call("mount -a", shell=True)
    time.sleep(10)
    print("Starting munge")
    subprocess.check_call('systemctl enable munge', shell=True)
    subprocess.check_call('systemctl start munge', shell=True)
    time.sleep(10)
    print("Starting slurmd and checking in")
    subprocess.check_call('systemctl enable slurmd', shell=True)
    subprocess.check_call('systemctl start slurmd', shell=True)



# Add user to docker group on workers
if __name__ == '__main__':
    main()
