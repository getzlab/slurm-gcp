#!/usr/bin/env python3

import argparse
import subprocess
import os
import json
import pandas as pd


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
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/apps/slurm/current/bin:/apps/slurm/current/sbin"
    # export gcloud credential path
    # os.environ["CLOUDSDK_CONFIG"] = subprocess.check_output(
    #   "echo -n ~slurm/.config/gcloud", shell = True
    # ).decode()
    #####################################

    hosts = subprocess.check_output('scontrol show hostnames {}'.format(' '.join(nodes)),shell=True).decode().rstrip().split('\n')

    if len(hosts):
        for machine_type, host_list in instance_manifest.loc[hosts].groupby('machine_type'):
            subprocess.check_call(
                'gcloud compute instances delete {hosts} --zone {zone} --quiet'.format(
                    hosts=' '.join(host_list.index),
                    zone=conf['compute_zone'],
                ),
                shell=True,
                stdin=subprocess.DEVNULL,
                executable='/bin/bash'
            )
            with open('/apps/slurm/scripts/suspend-resume.log', 'a') as w:
                for hostname in host_list:
                    w.write("Suspend {} ({})\n".format(hostname, machine_type))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('canine-suspend-instance')
    parser.add_argument(
        'nodes',
        nargs='+',
        help='Node names (or name ranges) to boot'
    )

    main(parser.parse_args().nodes)
