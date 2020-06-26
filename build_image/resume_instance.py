#!/usr/bin/env python3

import argparse
import subprocess
import os
import re
import json
import pandas as pd

gpu_pattern = re.compile(r'.*-xgpu-worker\d+')

def main(nodes):
    with open('/apps/slurm/current/etc/instance_conf.json') as r:
        conf = json.load(r)

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

    hosts = []
    gpu_hosts = {} # For mapping manifest names to hostnames
    print("Determining hostnames", nodes)
    for host in subprocess.check_output('scontrol show hostnames {}'.format(' '.join(nodes)), shell=True).decode().rstrip().split('\n'):
        if conf['gpu_count'] > 0 and gpu_pattern.match(host):
            gpu_hosts[host.replace('-xgpu-worker', '-worker')] = host
        else:
            hosts.append(host)
    print("Hostnames", hosts, gpu_hosts)

    if len(hosts):
        for machine_type, host_list in instance_manifest.loc[hosts].groupby('machine_type'):
            print("Resuming", host_list, machine_type)
            subprocess.check_call(
                'gcloud compute instances create {hosts} --async --labels canine=tgcp-worker,k9cluster={cluster} --boot-disk-size=50GB --boot-disk-type pd-standard'
                ' --image-project {project} --image-family canine-tgcp-worker-personalized '
                ' --scopes=https://www.googleapis.com/auth/cloud-platform '
                ' --metadata-from-file=startup-script=/apps/slurm/scripts/worker_wrapper.sh '
                ' --metadata=canine_conf_cluster_name={cluster},canine_conf_controller={controller},canine_conf_sec={sec} '
                ' --machine-type {machine_type} --zone {zone} {ip} {preemptible}'.format(
                    hosts=' '.join(host_list.index),
                    project=conf['project'],
                    cluster=conf['cluster'],
                    controller=conf['controller'],
                    sec=conf['sec'],
                    machine_type=machine_type,
                    zone=conf['compute_zone'],
                    ip="--no-address" if not conf['ip'] else '',
                    preemptible='--preemptible' if conf['preemptible'] else '',
                ),
                shell=True,
                stdin=subprocess.DEVNULL,
                executable='/bin/bash'
            )
            with open('/apps/slurm/scripts/suspend-resume.log', 'a') as w:
                for hostname in host_list.index:
                    w.write("Resume {} ({})\n".format(hostname, machine_type))


    if len(gpu_hosts):
        for machine_type, host_list in instance_manifest.loc[list(gpu_hosts.keys())].groupby('machine_type'):
            print("Resuming", host_list, machine_type)
            subprocess.check_call(
                'gcloud compute instances create {hosts} --async --labels canine=tgcp-worker,k9cluster={cluster} --boot-disk-size=50GB --boot-disk-type pd-standard'
                ' --image-project {project} --image-family canine-tgcp-worker-personalized '
                ' --scopes=https://www.googleapis.com/auth/cloud-platform '
                ' --metadata-from-file=startup-script=/apps/slurm/scripts/worker_wrapper.sh '
                ' --metadata=canine_conf_cluster_name={cluster},canine_conf_controller={controller},canine_conf_sec={sec}'
                ' --machine-type {machine_type} --zone {zone} --accelerator=type={gpu_type},count={gpu_count} {ip} {preemptible}'.format(
                    hosts=' '.join(gpu_hosts[host] for host in host_list.index),
                    project=conf['project'],
                    machine_type=machine_type,
                    zone=conf['compute_zone'],
                    gpu_type=conf['gpu_type'],
                    gpu_count=conf['gpu_count'],
                    cluster=conf['cluster'],
                    controller=conf['controller'],
                    sec=conf['sec'],
                    ip="--no-address" if not conf['ip'] else '',
                    preemptible='--preemptible' if conf['preemptible'] else '',
                ),
                shell=True,
                stdin=subprocess.DEVNULL,
                executable='/bin/bash'
            )
            with open('/apps/slurm/scripts/suspend-resume.log', 'a') as w:
                for hostname in host_list.index:
                    w.write("Resume {} ({})\n".format(hostname, machine_type))



if __name__ == '__main__':
    parser = argparse.ArgumentParser('canine-resume-instance')
    parser.add_argument(
        'nodes',
        nargs='+',
        help='Node names (or name ranges) to boot'
    )

    main(parser.parse_args().nodes)
