#!/bin/bash

(
  sudo apt-get update
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
  sudo apt-get install -y python dnsutils gcc git hwloc environment-modules \
    libhwloc-dev libibmad-dev libibumad-dev lua5.3 lua5.3-dev man2html \
    mariadb-server libmysqlclient-dev libmariadb-client-lgpl-dev munge \
    libmunge-dev libncurses-dev nfs-kernel-server numactl libnuma-dev libssl-dev \
    libpam-dev libextutils-makemaker-cpanfile-perl python python3-pip libreadline-dev \
    librrd-dev vim wget tcl tmux pdsh openmpi-bin

  cat > /lib/systemd/system/munge.service <<< "
[Unit]
Description=MUNGE authentication service
Documentation=man:munged(8)
After=network.target
After=syslog.target
After=time-sync.target

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

  systemctl enable munge
  create-munge-key -f

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
# CUDA_PATH=/usr/local/cuda
# PATH=$CUDA_PATH/bin${PATH:+:${PATH}}
# LD_LIBRARY_PATH=$CUDA_PATH/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
EOF

  mkdir -p /apps/modulefiles
  echo /apps/modulefiles >> /usr/share/modules/init/.modulespath

  systemctl start munge
  mkdir -p /apps/slurm/src
  cd /apps/slurm/src
  wget https://download.schedmd.com/slurm/slurm-18.08-latest.tar.bz2
  tar -xvjf slurm-18.08-latest.tar.bz2
  cd slurm-18.08.9/
  ./configure --prefix=$(pwd) --sysconfdir=/apps/slurm/current/etc --with-mysql_config=/usr/bin
  make -j install
  ln -s $(pwd) /apps/slurm/current
  mkdir -p /apps/slurm/current/etc
  chown -R slurm: /apps/slurm/current/etc
  mkdir -p /apps/slurm/state
  chown -R slurm: /apps/slurm/state
  mkdir -p /apps/slurm/log
  chown -R slurm: /apps/slurm/log

  cat > /lib/systemd/system/slurmctld.service <<\EOF
[Unit]
Description=Slurm controller daemon
After=network.target munge.service
ConditionPathExists=/apps/slurm/current/etc/slurm.conf

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/slurmctld
ExecStart=/apps/slurm/current/sbin/slurmctld $SLURMCTLD_OPTIONS
ExecReload=/bin/kill -HUP $MAINPID
PIDFile=/var/run/slurm/slurmctld.pid

[Install]
WantedBy=multi-user.target
EOF

  cat > /lib/systemd/system/slurmdbd.service <<\EOF
[Unit]
Description=Slurm DBD accounting daemon
After=network.target munge.service
ConditionPathExists=/apps/slurm/current/etc/slurmdbd.conf

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/slurmdbd
ExecStart=/apps/slurm/current/sbin/slurmdbd $SLURMDBD_OPTIONS
ExecReload=/bin/kill -HUP $MAINPID
PIDFile=/var/run/slurm/slurmdbd.pid

[Install]
WantedBy=multi-user.target
EOF

  systemctl enable mariadb
  systemctl enable slurmdbd
  systemctl enable slurmctld
  systemctl enable nfs-server

  echo "RPCNFSDCOUNT=256" | tee -a /etc/default/nfs-kernel-server

  cat > /etc/tmpfiles.d/slurm.conf <<\EOF
d /var/run/slurm  0755 slurm slurm -
EOF

  mkdir -p /var/run/slurm
  chown slurm: /var/run/slurm

) > /stdout.log 2> /stderr.log
