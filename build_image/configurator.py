"""
Prepares all nodes and startup scripts
"""

import argparse
import re
import subprocess
import os
import socket
import requests

placeholder = re.compile(r'\<(.+?)\>')

class Config(dict):
    def __init__(self, path):
        with open(path) as r:
            self.text = r.read()

        super().__init__({
            match.group(1): None
            for match in placeholder.finditer(self.text)
        })

    def dump(self):
        output = '' + self.text
        for key, val in self.items():
            if val is None:
                raise ValueError("Setting '{}' left blank".format(key))
            output = output.replace('<{}>'.format(key), val)
        return output

    def write(self, path):
        with open(path, 'w') as w:
            w.write(self.dump())

class Script(object):
    def __init__(self):
        self.lines = [
            '#!/bin/bash',
            'set -eo pipefail'
        ]

    def download_meta_file(self, key, path):
        self.lines += [
            'mkdir -p {}'.format(os.path.dirname(path)),
            'wget -O {path} --header="Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/{key}'.format(
                key=key,
                path=path
            )
        ]
        return self

class Instance(object):
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.startup_script = Script()


def main(cluster_name):
    controller = Instance(cluster_name+'-controller', 'controller')
    slurm_conf = Conf(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'conf-templates',
            'slurm.conf'
        )
    )
    slurm_conf['CONTROLLER HOSTNAME'] = controller.name
    slurm_conf['CLUSTER NAME'] = cluster_name
