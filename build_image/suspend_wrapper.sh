#!/bin/bash
python3 /apps/slurm/scripts/suspend_instance.py $@ </dev/null 2>> /apps/slurm/scripts/wrapper.log >> /apps/slurm/scripts/wrapper.log
