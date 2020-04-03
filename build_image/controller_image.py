import argparse
import subprocess

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser('update-controller-image')

    args = parser.parse_args()
