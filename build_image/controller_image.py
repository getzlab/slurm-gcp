import argparse
import subprocess
import time
import os
import tempfile
import crayons

def copyfile(instance, src, dest):
    subprocess.check_call(
        'gcloud compute scp {src} {instance}:{dest}'.format(instance, src, dest),
        shell=True
    )

def run_script(instance, path):
    subprocess.check_output(
        'gcloud compute ssh {instance} -- {path}'.format(instance, path),
        shell=True
    )

def main(name, mtype, zone, proj, image_name, image_family):
    print(crayons.green("Starting controller template...", bold=True))
    subprocess.check_call(
        'gcloud compute instances create {} --zone {} --project {} --machine-type {}'
        ' --image-project=ubuntu-os-cloud --image-family ubuntu-2004-lts'
        ' --metadata-from-file startup-script={}'.format(
            name,
            zone,
            proj,
            mtype,
            os.path.join(os.path.dirname(__file__), 'controller_script.sh')
        ),
        shell=True
    )
    killprocs = []
    try:
        print(crayons.green("Waiting for instance to start...", bold=True))
        time.sleep(10)
        while True:
            proc = subprocess.run(
                'gcloud compute ssh --zone {} --project {} {} -- [[ -e /stdout.log ]]'.format(zone, proj, name),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if proc.returncode == 0:
                break
            time.sleep(10)
        subprocess.check_call(
            'gcloud compute config-ssh',
            shell=True
        )
        print(crayons.green("Loading template stderr and stdout streams...", bold=True))
        time.sleep(5)
        stderr = subprocess.Popen(
            'gcloud compute ssh --zone {} --project {} {} -- tail -f /stderr.log'.format(zone, proj, name),
            shell=True
        )
        killprocs.append(stderr)
        stdout = subprocess.Popen(
            'gcloud compute ssh --zone {} --project {} {} -- tail -f /stdout.log'.format(zone, proj, name),
            shell=True
        )
        killprocs.append(stdout)
        time.sleep(15)
        while True:
            proc = subprocess.run(
                'gcloud compute ssh --zone {} --project {} {} -- [[ -d /apps ]]'.format(zone, proj, name),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if proc.returncode == 0:
                break
            time.sleep(10)
        print(crayons.green("Copying required scripts...", bold=True))
        files = {
            'slurm.conf': '/apps/slurm/scripts/conf-templates',
            'slurmdbd.conf': '/apps/slurm/scripts/conf-templates',
            'controller_start.py': '/apps/slurm/scripts',
            'resume_instance.py': '/apps/slurm/scripts',
            'suspend_instance.py': '/apps/slurm/scripts',
            'worker_start.py': '/apps/slurm/scripts',
            'resume_wrapper.sh': '/apps/slurm/scripts',
            'suspend_wrapper.sh': '/apps/slurm/scripts',
            'worker_wrapper.sh': '/apps/slurm/scripts'
        }
        for filename, dest in files.items():
            print(crayons.green("Copying", bold=True), filename, "->", dest)
            subprocess.check_call(
                'gcloud compute ssh --zone {} --project {} {} -- mkdir -p {}'.format(
                    zone,
                    proj,
                    name,
                    dest
                ),
                shell=True
            )
            subprocess.check_call(
                'gcloud compute scp --zone {} --project {} {} {}:{}'.format(
                    zone,
                    proj,
                    os.path.join(
                        os.path.dirname(__file__),
                        filename
                    ),
                    name,
                    dest
                ),
                shell=True
            )
        print(crayons.green("Waiting for installation to finish..", bold=True))
        while True:
            proc = subprocess.run(
                'gcloud compute ssh --zone {} --project {} {} -- [[ -e /apps/slurm/install.complete ]]'.format(zone, proj, name),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if proc.returncode == 0:
                break
            time.sleep(10)
        stderr.terminate()
        stdout.terminate()
        killprocs = []
        print(crayons.green("Configuring root ssh-key", bold=True))
        with tempfile.TemporaryDirectory() as tempdir:
            subprocess.check_call(
                'ssh-keygen -q -b 2048 -t rsa -f {}/id_rsa -N ""'.format(tempdir),
                shell=True
            )
            subprocess.check_call(
                'gcloud compute ssh --zone {} --project {} {} -- sudo mkdir -p /root/.ssh'.format(
                    zone,
                    proj,
                    name
                ),
                shell=True
            )
            subprocess.check_call(
                'cat {}/id_rsa.pub | gcloud compute ssh --zone {} --project {} {} -- sudo tee -a /root/.ssh/authorized_keys'.format(
                    tempdir,
                    zone,
                    proj,
                    name
                ),
                executable='/bin/bash',
                shell=True
            )
            print(crayons.green("Logging in as root to clean user directories", bold=True))
            print('ssh -i {tempdir}/id_rsa root@{instance}.{zone}.{project}'
                ' -- \'bash -c "sudo pkill -u {user}; userdel -rf {user} && rm /root/.ssh/authorized_keys"\''.format(
                    zone=zone,
                    project=proj,
                    tempdir=tempdir,
                    instance=name,
                    user=os.environ['USER'].strip()
            ))
            subprocess.check_call(
                'ssh -i {tempdir}/id_rsa root@{instance}.{zone}.{project}'
                ' -- \'bash -c "sudo pkill -u {user}; userdel -rf {user} && rm /root/.ssh/authorized_keys"\''.format(
                    zone=zone,
                    project=proj,
                    tempdir=tempdir,
                    instance=name,
                    user=os.environ['USER'].strip()
                ),
                shell=True,
                executable='/bin/bash'
            )
        print(crayons.green("Stopping template instance", bold=True))
        time.sleep(10)
        subprocess.check_call(
            'gcloud compute instances stop {} --zone {}'.format(
                name,
                zone
            ),
            shell=True
        )
        print(crayons.green("Generating image", bold=True))
        subprocess.check_call(
            'gcloud compute images create {} --source-disk {} --family {}'
            ' --description "Canine Transient GCP backend controller boot image" --source-disk-zone {}'.format(
                image_name,
                name,
                image_family,
                zone,
            ),
            shell=True
        )
    finally:
        for proc in killprocs:
            proc.terminate()
        print(crayons.green("Deleting template instance", bold=True))
        subprocess.check_call(
            'gcloud compute config-ssh --remove',
            shell=True
        )
        subprocess.check_call(
            'yes | gcloud compute instances delete {} --zone {}'.format(
                name,
                zone
            ),
            executable='/bin/bash',
            shell=True
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser('update-controller-image')
    parser.add_argument(
        'instance_name',
        help='templace instance name'
    )
    parser.add_argument(
        'instance_type',
        help='template instance type'
    )
    parser.add_argument(
        'instance_zone',
        help='template instance zone'
    )
    parser.add_argument(
        'project',
        help='Project'
    )
    parser.add_argument(
        'image_name',
        help='Final image name'
    )
    parser.add_argument(
        '-f', '--image-family',
        help='Template image family. Default:canine-tgcp-controller',
        default='canine-tgcp-controller'
    )

    args = parser.parse_args()
    main(args.instance_name, args.instance_type, args.instance_zone, args.project, args.image_name, args.image_family)

####
#1) Need to wrap suspend and resume
#2) Fix slurmd.service
