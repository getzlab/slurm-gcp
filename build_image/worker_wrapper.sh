#!/bin/bash
touch /worker_startup
python3 /opt/canine/worker_start.py < /dev/null > /startup.stdout.log 2> /startup.stderr.log
echo $? > /startup.rc
