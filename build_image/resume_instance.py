#!/usr/bin/env python3

import argparse
import subprocess
import os
import re
import json
import pandas as pd

gpu_pattern = re.compile(r'.*-xgpu-worker\d+')

def main(nodes):
    if os.path.exists('/apps/slurm/current/etc/instance_conf.json'):
        with open('/apps/slurm/current/etc/instance_conf.json') as r:
            conf = json.load(r)
    else:
        conf = {
            'gpu_type': '0',
            'gpu_count': 0,
            'compute_zone': 'us-central1-a',
            'startup_script': ''
        }

    instance_manifest = pd.read_csv('/apps/slurm/current/etc/instance_manifest.tsv', sep='\t', index_col=0)

    #####################################
    # Ported from Julian's Slurm-docker #
    #####################################
    # for some reason, the USER environment variable is set to root when this
    # script is run, even though it's run under user slurm ...
    os.environ["USER"] = "slurm"

    # export gcloud credential path
    os.environ["CLOUDSDK_CONFIG"] = subprocess.check_output(
      "echo -n ~slurm/.config/gcloud", shell = True
    ).decode()
    #####################################

    hosts = []
    gpu_hosts = []
    for host in subprocess.check_output('scontrol show hostnames {}'.format(' '.join(nodes)),shell=True).decode().rstrip().split('\n'):
        if gpu_count > 0 and gpu_pattern.match(host):
            gpu_hosts.append((host, host.replace('-xgpu-worker', '-worker')))
        else:
            hosts.append(host)

    for machine_type, host_list in instance_manifest.loc[hosts].groupby('machine_type'):
        subprocess.check_call(
            'gcloud compute instances create {hosts} --image {image}'
            ' --machine-type {machine_type} --zone {zone}'
        )




if __name__ == '__main__':
    parser = argparse.ArgumentParser('canine-resume-instance')
    parser.add_argument(
        'nodes',
        nargs='+',
        help='Node names (or name ranges) to boot'
    )

    main(parser.parse_args().nodes)
