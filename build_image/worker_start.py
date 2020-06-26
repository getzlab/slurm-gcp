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
    with open('/lib/systemd/system/slurmd.service', 'w') as w:
        w.write(
"""
[Unit]
Description=Slurm node daemon
After=network.target munge.service
ConditionPathExists=/apps/slurm/current/etc/slurm.conf

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/slurmd
ExecStart=/apps/slurm/current/sbin/slurmd $SLURMD_OPTIONS
ExecReload=/bin/kill -HUP $MAINPID
PIDFile=/var/run/slurm/slurmd.pid
KillMode=process
LimitNOFILE=51200
LimitMEMLOCK=infinity
LimitSTACK=infinity

[Install]
WantedBy=multi-user.target
"""
        )
    with open('/lib/systemd/system/slurmd.service') as r:
        print(r.read())
    subprocess.run('systemctl disable slurmd', shell=True)
    subprocess.run('systemctl stop slurmd', shell=True)
    instance_name = read_meta_key('instance/name')
    cluster = read_meta_key('instance/attributes/canine_conf_cluster_name')
    controller = read_meta_key('instance/attributes/canine_conf_controller')
    sec = read_meta_key('instance/attributes/canine_conf_sec')
    print("Starting worker", instance_name, "as part of cluster", cluster)
    print("Mounting NFS volumes")
    with open('/etc/fstab', 'a') as w:
        w.write('{}:/apps\t/apps\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        w.write('{}:/etc/munge\t/etc/munge\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        w.write('{}:/home\t/home\tnfs\trw,hard,intr\t0\t0\n'.format(controller))
        if len(sec) and sec != '-':
            w.write('{0}:{1}\t{1}\tnfs\trw,hard,intr\t0\t0\n'.format(controller, sec))
    subprocess.check_call('rm -rf /home/*', shell=True)
    subprocess.check_call("mount -a", shell=True)
    time.sleep(30)
    subprocess.check_call('bash /apps/slurm/scripts/custom_worker_start.sh', shell=True)
    print("Starting munge")
    subprocess.check_call('systemctl enable munge', shell=True)
    subprocess.check_call('systemctl start munge', shell=True)
    time.sleep(10)
    subprocess.check_call('mkdir -p /var/log/slurm/ /var/run/slurm /var/spool/slurmd', shell=True)
    subprocess.check_call('chown -R slurm: /var/log/slurm/ /var/run/slurm /var/spool/slurmd', shell=True)
    subprocess.run('pkill slurm', shell=True)
    time.sleep(10)
    subprocess.check_call('systemctl restart munge', shell=True)
    time.sleep(10)
    print("Starting slurmd and checking in")
    subprocess.check_call('systemctl enable slurmd', shell=True)
    for i in range(3):
        try:
            subprocess.check_call('systemctl start slurmd', shell=True)
            break
        except subprocess.CalledProcessError:
            print("Failed to boot slurmd on attempt", i+1)
            time.sleep(10)
            subprocess.run('systemctl stop slurmd', shell=True)
            subprocess.run('pkill slurm', shell=True)
            time.sleep(10)



# Add user to docker group on workers
if __name__ == '__main__':
    main()
