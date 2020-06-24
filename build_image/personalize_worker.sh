#!/bin/bash
sudo usermod -a -G docker $(whoami)
echo {0}$'\t'ALL='(ALL:ALL)'$'\t'NOPASSWD:$'\t'ALL | sudo tee -a /etc/sudoers
