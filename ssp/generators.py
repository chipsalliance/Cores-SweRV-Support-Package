import functools
import logging
import pathlib
import os
import shutil
import subprocess
from string import Template
from ssp import exceptions

from ssp.exceptions import Exceptions

import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper


user_template = Template("""
RUN set -eux && getent group $username || groupadd -f $username -g $gid \\
    && useradd --create-home --no-log-init -u $uid -g $gid $username \\
    && echo '$username:$username' | chpasswd \\
    && echo 'export MODULEPATH=/prj/ssp/modules' >> /home/$username/.bashrc \\
    && echo '$username ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers\n
""")

user_tamplate_add_groups = Template("""
RUN usermod -aG $usergroups $username\n
""")


def test_wrapper(function):
    # Wrapper that checks if docker is installed and user has proper rights, by calling docker info
    @functools.wraps(function)
    def test_docker_installation(*args, **kwargs):
        if subprocess.run(['docker', 'info'], stdout=open(os.devnull, 'wb')).returncode != 0:
            raise Exceptions.DockerException(
                "Docker is not properly installed.")
        return function(*args, **kwargs)
    return test_docker_installation


class Dockergen:
    def __init__(self, config, current_user):
        self.config = config
        self.current_user = current_user

    def generate_dockerfile(self, where, skip_config, run_uid, run_gid):
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

            # Groups specification
            if 'groups' in self.config:
                # Create all groups first
                for group_name, group_id in self.config['groups'].items():
                    dockerfile.write(
                        f"RUN groupadd {group_name} -g {group_id}\n")
                dockerfile.write("\n")

            # Users with uids, gids, groups and shell
            if 'users' in self.config:
                # Creating all users with appropriate uid an gid, along with custom shell
                for user in self.config['users']:
                    dockerfile.write(user_template.substitute(
                        username=user['name'], uid=user['uid'], gid=user['gid']))

                    if 'groups' in user:
                        dockerfile.write(user_tamplate_add_groups.substitute(
                            usergroups=','.join(str(x) for x in user['groups']), username=user['name']))

                    # Get shell user wants to use
                    # if user['name'] == self.current_user:
                    #     self.shell = user['shell']
                dockerfile.write("\n")

            # Mount drives
            if 'drives' in self.config:
                # Mount all the drives
                dockerfile.write("RUN touch /etc/fstab\n")
                for drive, mount in self.split_items_list(self.config['drives']):
                    dockerfile.write(
                        f"RUN mkdir -p {mount}"
                        f" && echo '{drive} {mount} nfs defaults 0 0' >> /etc/fstab\n")
                dockerfile.write("\n")

            if 'copyfiles' in self.config:
                for file_source, file_target in self.split_items_list(self.config['copyfiles']):
                    # Local file has to be copied to the same directory as dockerfile.
                    source = pathlib.Path(file_source).expanduser()
                    if not source.is_absolute():
                        source = source.absolute()
                    if not source.exists():
                        logging.error("Source target does not exist, skipping copying file %s" % source)
                        continue
                    
                    # TODO 
                        
                    # Do not copy file to dockerfile location if they are in the same dir as 
                    # shutil will raise samefile error
                    if source.parent != where:
                        shutil.copy2(str(source), str(where))

                    # Expand user for target as well
                    target = pathlib.Path(file_target).expanduser()

                    # Create copy command with source name only since it is in the same dir.
                    dockerfile.write(f"COPY {source.name} {target}\n")

                dockerfile.write("\n")

            # Symlinks
            if 'symlinks' in self.config:
                for symlink in self.split_items_list(self.config['symlinks']):
                    dockerfile.write(f"RUN ln -s {symlink[0]} {symlink[1]}\n")

            # Exports
            if 'export' in self.config:
                for item in self.config['export']:
                    dockerfile.write(f"ENV {item}\n")
                dockerfile.write("\n")

            dockerfile.write(
                f"RUN chown {run_uid}:{run_gid} /prj/ssp /prj/ssp/** /prj/ssp/.cpm\n")
            # Set user
            if skip_config:
                dockerfile.write(f"RUN cpm init -y --skip-config\n")
            else:
                dockerfile.write(f"RUN cpm init -y\n")
            dockerfile.write("\n")
            dockerfile.write(f"USER {self.current_user}\n")
            dockerfile.write(f"WORKDIR /home/{self.current_user}\n")
            dockerfile.write(
                f"CMD sudo mount -a & sudo /usr/sbin/sshd -D & /bin/bash\n")
            dockerfile.write("\n")

    @classmethod
    def split_items_list(self, items):
        for item in items:
            split_list = list(filter(lambda x: len(x) > 0, item.split(" ")))
            if len(split_list) != 2:
                raise exceptions.Exceptions().SSPSetupError("An error ocured while parsing yaml input.\n Error ocured while parsing: %s" % items)
            yield split_list


class Yamlgen:
    def __init__(self, yaml_name, yaml_path):
        self.yaml_name = yaml_name
        self.yaml_path = yaml_path

    def generate_yamlfile(self, ssp_yaml, indent=4):
        with open(str(self.yaml_path.joinpath(self.yaml_name)), 'w') as fp:
            yaml.dump(ssp_yaml, fp, Dumper=Dumper, indent=indent,
                      default_flow_style=False,  allow_unicode=True, sort_keys=False)
