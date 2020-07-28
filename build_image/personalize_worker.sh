#!/bin/bash
sudo systemctl disable slurmd
whoami
sudo usermod -a -G docker $(whoami)
echo $(whoami)$'\t'ALL='(ALL:ALL)'$'\t'NOPASSWD:$'\t'ALL | sudo tee -a /etc/sudoers
ls -l /lib/systemd/system/slurmd.service
