#!/bin/bash
sudo systemctl disable slurmd
sudo usermod -a -G docker $(whoami)
echo {0}$'\t'ALL='(ALL:ALL)'$'\t'NOPASSWD:$'\t'ALL | sudo tee -a /etc/sudoers
ls -l /lib/systemd/system/slurmd.service
