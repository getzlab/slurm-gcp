#!/bin/bash
python3 /apps/slurm/scripts/resume_instance.py $@ </dev/null 2>&1 >> /apps/slurm/scripts/wrapper.log
