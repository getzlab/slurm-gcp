#!/bin/bash

(
  sudo apt-get update
  touch /poop
  cat > /etc/motd <<< "
                                 SSSSSSS
                                SSSSSSSSS
                                SSSSSSSSS
                                SSSSSSSSS
                        SSSS     SSSSSSS     SSSS
                       SSSSSS               SSSSSS
                       SSSSSS    SSSSSSS    SSSSSS
                        SSSS    SSSSSSSSS    SSSS
                SSS             SSSSSSSSS             SSS
               SSSSS    SSSS    SSSSSSSSS    SSSS    SSSSS
                SSS    SSSSSS   SSSSSSSSS   SSSSSS    SSS
                       SSSSSS    SSSSSSS    SSSSSS
                SSS    SSSSSS               SSSSSS    SSS
               SSSSS    SSSS     SSSSSSS     SSSS    SSSSS
          S     SSS             SSSSSSSSS             SSS     S
         SSS            SSSS    SSSSSSSSS    SSSS            SSS
          S     SSS    SSSSSS   SSSSSSSSS   SSSSSS    SSS     S
               SSSSS   SSSSSS   SSSSSSSSS   SSSSSS   SSSSS
          S    SSSSS    SSSS     SSSSSSS     SSSS    SSSSS    S
    S    SSS    SSS                                   SSS    SSS    S
    S     S                                                   S     S
                SSS
                SSS
                SSS
                SSS
 SSSSSSSSSSSS   SSS   SSSS       SSSS    SSSSSSSSS   SSSSSSSSSSSSSSSSSSSS
SSSSSSSSSSSSS   SSS   SSSS       SSSS   SSSSSSSSSS  SSSSSSSSSSSSSSSSSSSSSS
SSSS            SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSS            SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSS    SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
 SSSSSSSSSSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
         SSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
         SSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSSS   SSS   SSSSSSSSSSSSSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSS    SSS    SSSSSSSSSSSSS    SSSS        SSSS     SSSS     SSSS

"
  groupadd -g 992 slurm
  useradd -m -c "SLURM Workload Manager" -d /var/lib/slurm -u 992 -g slurm -s /bin/bash slurm

  mkdir -p /apps
  chown -R slurm: /apps
  chmod -R a+rX /apps
  mkdir -p /opt/canine
  chown -R slurm: /opt/canine
  chmod -R 777 /opt/canine
  mkdir -p /var/log/slurm/ /var/spool/slurmd
  chown -R slurm: /var/log/slurm/ /var/spool/slurmd

  sudo apt-get install -y python dnsutils gcc git hwloc environment-modules \
    libhwloc-dev libibmad-dev libibumad-dev lua5.3 lua5.3-dev man2html \
    mariadb-server libsqlclient-dev libmariadb-dev munge \
    libmunge-dev libncurses-dev nfs-kernel-server numactl libnuma-dev libssl-dev \
    libpam-dev libextutils-makemaker-cpanfile-perl python python3-pip libreadline-dev \
    librrd-dev vim wget tcl tmux pdsh openmpi-bin wget htop docker.io

  mkdir /opt/cuda
  cd /opt/cuda
  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-repo-ubuntu1804_10.0.130-1_amd64.deb
  dpkg -i cuda-repo-ubuntu1804_10.0.130-1_amd64.deb
  apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
  apt-get update
  wget https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/nvidia-machine-learning-repo-ubuntu1804_1.0.0-1_amd64.deb
  apt-get install -y ./nvidia-machine-learning-repo-ubuntu1804_1.0.0-1_amd64.deb
  apt-get update
  apt-get install -y --no-install-recommends nvidia-driver-410
  apt-get install -y --no-install-recommends cuda-10-0 libcudnn7=7.4.1.5-1+cuda10.0 libcudnn7-dev=7.4.1.5-1+cuda10.0
  apt-get update
  apt-get install -y --allow-unauthenticated nvinfer-runtime-trt-repo-ubuntu1804-5.0.2-ga-cuda10.0
  apt-get update
  apt-get install -y --no-install-recommends libnvinfer-dev
  rm cuda-repo-ubuntu1804_10.0.130-1_amd64.deb
  rm nvidia-machine-learning-repo-ubuntu1804_1.0.0-1_amd64.deb
  nvidia-smi


  cat > /lib/systemd/system/slurmd.service <<< "
[Unit]
Description=Slurm node daemon
After=network.target munge.service
ConditionPathExists=/apps/slurm/current/etc/slurm.conf

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/slurmd
ExecStart=/apps/slurm/current/sbin/slurmd \$SLURMD_OPTIONS
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/slurm/slurmd.pid
KillMode=process
LimitNOFILE=51200
LimitMEMLOCK=infinity
LimitSTACK=infinity

[Install]
WantedBy=multi-user.target
"

cat > /opt/slurmd_test_service <<< "
[Unit]
Description=Slurm node daemon
After=network.target munge.service
ConditionPathExists=/apps/slurm/current/etc/slurm.conf

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/slurmd
ExecStart=/apps/slurm/current/sbin/slurmd \$SLURMD_OPTIONS
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/slurm/slurmd.pid
KillMode=process
LimitNOFILE=51200
LimitMEMLOCK=infinity
LimitSTACK=infinity

[Install]
WantedBy=multi-user.target
"

  cat > /lib/systemd/system/munge.service <<< "
[Unit]
Description=MUNGE authentication service
Documentation=man:munged(8)
After=network.target
After=syslog.target
After=time-sync.target
RequiresMountsFor=/etc/munge

[Service]
Type=forking
ExecStart=/usr/sbin/munged --num-threads=10
PIDFile=/var/run/munge/munged.pid
User=munge
Group=munge
Restart=on-abort

[Install]
WantedBy=multi-user.target
"
  cat > /etc/profile <<\EOF
  # /etc/profile: system-wide .profile file for the Bourne shell (sh(1))
  # and Bourne compatible shells (bash(1), ksh(1), ash(1), ...).
  if [ "${PS1-}" ]; then
    if [ "${BASH-}" ] && [ "$BASH" != "/bin/sh" ]; then
      # The file bash.bashrc already sets the default PS1.
      # PS1='\h:\w\$ '
      if [ -f /etc/bash.bashrc ]; then
        . /etc/bash.bashrc
      fi
    else
      if [ "`id -u`" -eq 0 ]; then
        PS1='# '
      else
        PS1='$ '
      fi
    fi
  fi
EOF

  cp /etc/bash.bashrc /etc/bash.bashrc.bak
  cat > /etc/bash.bashrc <<\EOF
  # Shim to load profile.d always
  for i in /etc/profile.d/*.sh; do
  if [ -r "$i" ]; then
      if [ "${-#*i}" != "$-" ]; then
          . "$i"
      else
          . "$i" >/dev/null
      fi
  fi
  done
EOF

  cat /etc/bash.bashrc.bak >> /etc/bash.bashrc

  cat > /etc/profile.d/slurm.sh <<\EOF
S_PATH=/apps/slurm/current
PATH=$PATH:$S_PATH/bin:$S_PATH/sbin
CUDA_PATH=/usr/local/cuda
PATH=$CUDA_PATH/bin${PATH:+:${PATH}}
LD_LIBRARY_PATH=$CUDA_PATH/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
EOF


  systemctl enable nfs-server

  echo "RPCNFSDCOUNT=256" | tee -a /etc/default/nfs-kernel-server

  echo '*/2 * * * * if [ `systemctl status slurmd | grep -c inactive` -gt 0 ]; then mount -a; systemctl restart slurmd; fi' | crontab -u root -
  sed -e 's/GRUB_CMDLINE_LINUX="\\?\\([^"]*\\)"\\?/GRUB_CMDLINE_LINUX="\\1 cgroup_enable=memory swapaccount=1"/' < /etc/default/grub > grub.tmp
  sudo mv grub.tmp /etc/default/grub
  sudo grub-mkconfig -o /etc/grub2.cfg

  mkdir -p /var/run/slurm
  chown slurm: /var/run/slurm

  dd if=/dev/zero of=/swapfile count=4096 bs=1MiB
  chmod 700 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | tee -a /etc/fstab

  umask 022
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python2 get-pip.py
  rm get-pip.py
  python2 -m pip uninstall -y crcmod
  python2 -m pip install --no-cache-dir -U crcmod
  python3 -m pip install requests pandas google-auth google-api-python-client crcmod

  apt-get update
  apt install -y  gce-compute-image-packages google-compute-engine-oslogin python3-google-compute-engine
  apt autoremove -y

  systemctl disable slurmd

  touch /opt/install.complete


) > /stdout.log 2> /stderr.log
