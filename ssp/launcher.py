import functools
import json
import logging
import pathlib
import os
import subprocess
from string import Template

import docker
import inquirer
import getpass
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from ssp import exceptions

# ==============================================================================
# DO NOT CHANGE CODE ABOVE, MODIFY VARIABLES BELLOW ONLY

# CONFIG_NAME and CONFIG_PATH can also be exported as environment variables
SSP_CONFIG_NAME = pathlib.Path(os.environ["SSP_CONFIG_NAME"]) if "SSP_CONFIG_NAME" in os.environ else pathlib.Path(
    'ssp.yaml')
SSP_CONFIG_PATH = pathlib.Path(os.environ["SSP_CONFIG_PATH"]) if "SSP_CONFIG_PATH" in os.environ else pathlib.Path(
    '.')
SSP_CONFIG_PATH = SSP_CONFIG_PATH.joinpath(SSP_CONFIG_NAME)
SSP_DOCKERFILE_PATH = os.environ["SSP_DOCKERFILE_PATH"] if "SSP_DOCKERFILE_PATH" in os.environ else pathlib.Path.home(
).joinpath('tmp')

# DO NOT CHANGE CODE BELLOW, MODIFY VARIABLE ABOVE ONLY
# ==============================================================================+


user_template = Template("""
RUN set -eux && getent group $username || groupadd -f $username -g $gid \\
    && useradd --create-home --no-log-init -u $uid -g $gid $username \\
    && echo '$username:$username' | chpasswd \\
    && echo 'export MODULEPATH=/prj/ssp/modules' >> /home/$username/.bashrc \\
    && usermod -aG $usergroups $username \\
    && echo '$username ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers\n
""")


def test_wrapper(function):
    # Wrapper that checks if docker is installed and user has proper rights, by calling docker info
    @functools.wraps(function)
    def test_docker_installation(*args, **kwargs):
        if subprocess.run(['docker', 'info'], stdout=open(os.devnull, 'wb')).returncode != 0:
            raise exceptions.DockerException(
                "Docker is not properly installed.")
        return function(*args, **kwargs)
    return test_docker_installation


class SSP_Launcher:
    def __init__(self, config_path=SSP_CONFIG_PATH, debug=False):
        self.config_path = config_path
        self.config = None

        self.current_user = getpass.getuser()
        self.shell = None
        loglevel = logging.DEBUG if debug else logging.INFO
        self._init_logging(loglevel)

        self.registry_url = "ssp-docker-registry.codasip.com"
        self.registry_url_cn = "ssp-docker-registry-cn.codasip.com:5443"

    @test_wrapper
    def download(self, version):
        # Chineese users cannot download from EU server, therefore this option.
        region = inquirer.prompt([inquirer.List('region', message="Select your region: ",
                                                choices=['EU/US', 'CN'], default=['EU/US'])])['region']
        logging.debug("%s" % region)

        # As of 2020, Codasip has two docker registries - one in Europe and one in China.
        # Also there is furture possibility for more than one publicly avialable distribution.
        distributions = {'eu': {
            'free': '/free/distrib-ssp-seh1-free'
        }, 'cn': {
            'free': '/distrib-ssp-seh1-free'
        }}
        # Choose distribution (now only free is avail) and region.
        distribution = distributions['cn']['free'] if region == 'CN' else distributions['eu']['free']
        registry_url = self.registry_url_cn if region == 'CN' else self.registry_url
        # Get full url to download docker image from.
        image_url = registry_url + distribution + ":" + version
        # Pull docker image using subprocess rather than docker module.
        if subprocess.run(['docker', 'pull', image_url]).returncode != 0:
            raise exceptions.DockerException(
                "Could not pull specified docker image.")
        logging.info("Successfuly downloaded docker image: %s" % image_url)

    def generate_dockerfile(self, where, skip_config):
        """Generate Dockerfile with instructions to copy packages into SSP.

        :param where: Path where the Docker context directory is.
        :type where: pathlib.Path
        :param from_image: Base Docker image for the Dockerfile.
        :type from_image: str
        :param packages: List of built packages to include into Docker.
        :type packages: [ArchivedPackage]
        :param master_metadata: Master metadata file for SSP (package.json)
        :type master_metadata: pathlib.Path
        """
        
        logging.info("Generating context for Docker build")
        if not where.is_dir():
            where.mkdir(parents=True, exist_ok=True)

        logging.info("Generating Dockerfile")
        with (where / 'Dockerfile').open('w') as dockerfile:
            # We are creating am image from distribution image
            dockerfile.write(f"FROM {self.config['from_image']}\n")
            dockerfile.write("USER root\n")
            dockerfile.write("\n")

            if self.config['groups'] is not None:
                # Create all groups first
                for group_name, group_id in self.config['groups'].items():
                    dockerfile.write(
                        f"RUN groupadd {group_name} -g {group_id}\n")
                dockerfile.write("\n")

            if self.config['users'] is not None:
                # Creating all users with appropriate uid an gid, along with custom shell
                for user in self.config['users']:
                    dockerfile.write(user_template.substitute(
                        username=user['name'], uid=user['uid'], gid=user['gid'],
                        usergroups=','.join(str(x) for x in user['groups'])
                    ))
                    # Get shell user wants to use
                    # if user['name'] == self.current_user:
                    #     self.shell = user['shell']
                dockerfile.write("\n")

            if self.config['drives'] is not None:
                # Mount all the drives
                dockerfile.write("RUN sudo touch /etc/fstab\n")
                for drive in self.split_items_list(self.config['drives']):
                    dockerfile.write(
                        f"RUN mkdir -p {drive[1]}"
                        f"&& echo '{drive[0]} {drive[1]} nfs defaults 0 0' >> /etc/fstab\n")
                dockerfile.write("\n")

            if self.config['symlinks'] is not None:
                for symlink in self.split_items_list(self.config['symlinks']):
                    dockerfile.write(f"RUN ln -s {symlink[0]} {symlink[1]}\n")

            if self.config['export'] is not None:
                for item in self.config['export']:
                    dockerfile.write(f"ENV {item}\n")
                dockerfile.write("\n")

            # Set user
            dockerfile.write(f"USER {self.current_user}\n")
            dockerfile.write(
                f"RUN sudo chown {self.current_user}:{self.current_user} /prj/ssp /prj/ssp/** /prj/ssp/.cpm\n")
            if skip_config:
                dockerfile.write(f"RUN cpm init -y --skip-config\n")
            else:
                dockerfile.write(f"RUN cpm init -y\n")
            dockerfile.write("\n")
            dockerfile.write(f"WORKDIR /home/{self.current_user}\n")
            dockerfile.write(
                f"CMD sudo mount -a & sudo /usr/sbin/sshd -D & /bin/bash\n")
            dockerfile.write("\n")

    @test_wrapper
    def run(self, sshx, dry_run, skip_config):
        if not self.config_path.exists():
            raise exceptions.ConfigurationError(
                f"Invalid path to config: {self.config_path}")

        with open(self.config_path) as fp:
            self.config = yaml.load(fp, Loader=Loader)

        if self.current_user not in self.list_usernames():
            logging.error(
                "Current user is not in ssp.yaml. Create entry and try again.")
            return

        # Generate docker file
        logging.info("Generating Dockerfile.")
        self.generate_dockerfile(SSP_DOCKERFILE_PATH, skip_config)
        # Build docker image from new docker file
        logging.info("Building Docker image")
        subprocess.run(['docker', 'build', str(SSP_DOCKERFILE_PATH),
                        '-t', self.config['new_image']], check=True)
        logging.info("Docker image successfuly built.")

        if dry_run:
            logging.info("Generated dockerfile to: %s" % SSP_DOCKERFILE_PATH)
            return

        # Run newly built docker image
        logging.info("Starting docker container.")
        if sshx:
            # If the X-server is needed, docker container has to be started in detached mode,
            # and connected to via ssh -x
            # docker hash is needed to get docker IP. Also we only need first 12 chars from string.
            docker_hash = subprocess.run(['docker', 'run', '-dt', '--rm',
                                          '--privileged', '-p', '22', self.config['new_image']], stdout=subprocess.PIPE).stdout.decode('utf-8')[:12]
            logging.debug(docker_hash)
            # Get docker IP
            client = docker.DockerClient()
            docker_ip = client.containers.get(
                docker_hash).attrs['NetworkSettings']['IPAddress']
            subprocess.run(['ssh', '-X', f"{self.current_user}@{docker_ip}"])
        else:
            # If -x is not needed, connect the usual way.
            subprocess.run(['docker', 'run', '-it', '--rm',
                            '--privileged', self.config['new_image']])

    def list_usernames(self):
        return [user['name'] for user in self.config['users']]

    @classmethod
    def split_items_list(cls, items):
        return list(item.split(' ') for item in items)

    def _init_logging(self, level):
        """Initialize loggers.
        : param level: Logging level.
        : type level: int
        """
        logging.basicConfig(
            format="%(asctime)s %(levelname)s [%(name)s]: %(message)s")

        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s]: %(message)s',
            '%d.%m.%Y: %H%M%S')

        logger = logging.getLogger()
        logger.setLevel(level)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
