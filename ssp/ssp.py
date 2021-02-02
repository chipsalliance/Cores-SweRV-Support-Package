import logging
import pathlib
import os
import shutil
import subprocess
import sys
import tempfile

import docker
import getpass
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from collections import OrderedDict

from ssp import generators, config
from ssp.exceptions import Exceptions


class SSP_Launcher:
    def __init__(self, config_path=config.SSP_CONFIG_PATH, debug=False, require_yaml_exists=True):
        self.debug = debug
        loglevel = logging.DEBUG if self.debug else logging.INFO
        self._init_logging(loglevel)
        # Hide traceback, except in Debug mode
        sys.tracebacklimit = 1000 if self.debug else 0

        self.config_path = config_path
        if require_yaml_exists and not self.config_path.exists():
            raise Exceptions.ConfigurationError(
                f"Invalid path to config: {self.config_path}. If it does not exists, try `ssp generate`")

        if self.config_path.exists():
            with open(self.config_path) as fp:
                self.config = yaml.load(fp, Loader=Loader)

        self.current_user = getpass.getuser()
        self.cwd = pathlib.Path().cwd()
        self.shell = None

        self.registry_url = "ssp-docker-registry.codasip.com"
        self.registry_url_cn = "ssp-docker-registry-cn.codasip.com:5443"

    @Exceptions.test_wrapper
    def download(self, version, region):
        # Chineese users cannot download from EU server, therefore this option.

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
            raise Exceptions.DockerException(
                "Could not pull specified docker image")
        logging.info("Successfuly downloaded docker image: %s" % image_url)

    @Exceptions.test_wrapper
    def setup(self, output, *args, **kwargs):
        logging.info("Generating ssp.yaml file...")

        ssp_yaml = dict()
        ssp_yaml['from_image'] = kwargs['setup_docker_url']
        ssp_yaml['new_image'] = kwargs['setup_docker_name']

        if 'setup_groups' in kwargs:
            ssp_yaml['groups'] = dict((key, value)
                                      for (key, value) in kwargs['setup_groups'])
        logging.debug([dict(user) for user in kwargs['setup_users']])
        ssp_yaml['users'] = [dict(user) for user in kwargs['setup_users']]

        if 'setup_drives' in kwargs:
            ssp_yaml['drives'] = [f"{dsource} {dtarget}" for (
                dsource, dtarget) in kwargs['setup_drives']]
        if 'setup_symlinks' in kwargs:
            ssp_yaml['symlinks'] = [f"{ssource} {starget}" for (
                ssource, starget) in kwargs['setup_symlinks']]
        if 'setup_copyfiles' in kwargs:
            ssp_yaml['copyfiles'] = [f"{cfsource} {cftarget}" for (
                cfsource, cftarget) in kwargs['setup_copyfiles']]

        if 'setup_env_vars' in kwargs:
            ssp_yaml['export'] = [
                variable for variable in kwargs['setup_env_vars']]

        logging.debug("SSP YAML raw structure: %s" % ssp_yaml)
        yaml_path = self.cwd
        yaml_name = output

        logging.info("Creating yaml file in: %s" % yaml_path)
        yamlgen = generators.Yamlgen(yaml_name, yaml_path)
        yamlgen.generate_yamlfile(ssp_yaml)
        logging.info("Finished generating yaml to: %s" % yaml_path)

        return yaml_path, yaml_name

    @Exceptions.test_wrapper
    def run(self, sshx, dry_run, skip_config):
        if self.current_user not in self._list_usernames():
            raise Exceptions.SSPSetupError(
                "Current user is not in ssp.yaml. Create entry and try again")

        # Generate docker file
        logging.info("Starting SSP run process")
        dockergen = generators.Dockergen(self.config, self.current_user)

        ssp_dockerfile_path = config.SSP_DOCKERFILE_PATH
        if dry_run:
            ssp_dockerfile_path = self.cwd
            os.environ["SSP_DOCKERFILE_PATH"] = str(self.cwd)
            logging.info("Set env variable 'SSP_DOCKERFILE_PATH' to %s" %
                         ssp_dockerfile_path)

        run_uid, run_gid = self._get_uid_gid()
        dockergen.generate_dockerfile(
            ssp_dockerfile_path, skip_config, run_uid, run_gid)
        if dry_run:
            logging.info("Generated dockerfile to: %s. Exiting" %
                         ssp_dockerfile_path)
            return
        else:
            self.run_start(sshx)

    def run_from_file(self, sshx):
        cwd = pathlib.Path.cwd()
        if not 'Dockerfile' in os.listdir(cwd):
            raise Exceptions.SSPSetupError(
                "Dockerfile not present in current folder, cannot start in --from-file mode.")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                shutil.copy2(pathlib.Path(cwd, 'Dockerfile'),
                             pathlib.Path(tmpdir, 'Dockerfile'))
                config.SSP_DOCKERFILE_PATH = tmpdir
            except PermissionError:
                raise Exceptions.DockerException(
                    "Unable to start docker from file. Unable to copy Dockerfile to temporary directory.")
            self.run_start(sshx)

    def run_start(self, sshx):
        if self.current_user not in self._list_usernames():
            raise Exceptions.SSPSetupError(
                "Current user is not in ssp.yaml. Create entry and try again.")

        # Build docker image from new docker file
        logging.info("Building Docker image")
        subprocess.run(['docker', 'build', str(config.SSP_DOCKERFILE_PATH),
                        '-t', self.config['new_image']], check=True)
        logging.info("Docker image successfuly built")

        # Run newly built docker image
        logging.info("Starting docker container")
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

    @classmethod
    def split_items_list(cls, items):
        return list(filter(lambda x: len(x) > 0, items.split(" ")))

    @classmethod
    def read_envvar_file(cls, envvar_path):
        with open(envvar_path, 'r') as file:
            for line in file:
                yield line.strip('\n')

    def _list_usernames(self):
        return [user['name'] for user in self.config['users']]

    def _get_uid_gid(self):
        for user in self.config['users']:
            if user['name'] == self.current_user:
                return user['uid'], user['gid']
        raise Exceptions.SSPSetupError(
            "Unable to find uid and gid for current user in users definition.")

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


class User:
    def __init__(self, name=None, uid=None, gid=None, groups=[], shell=None):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.groups = groups
        self.shell = shell

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if value:
                yield attr, value
            else:
                continue
