import logging
import os
import pathlib
import time

import click
import inquirer

import ssp as ssp_base

from ssp import ssp as ssp_module, config
from ssp.ssp import User


@click.group()
def ssp():
    """ Codasip Launcher for SSP."""


@ssp.command()
@click.option('-v', '--version', type=str, default='latest', help="Optional. Other version tha latest can be downloaded.")
@click.option('--debug', is_flag=True)
def download(version, debug):
    launcher = ssp_module.SSP_Launcher(debug=debug)
    region = inquirer.prompt([inquirer.List('region', message="Select your region: ",
                                            choices=['EU/US', 'CN'], default=['EU/US'])])['region']
    launcher.download(version, region)


@ssp.command()
@click.option('-i', '--interactive',
              help="Interactive mode ", is_flag=True)
@click.option('-o', '--output', 'output_name', type=str, default="", )
@click.option('--debug', is_flag=True)
def generate(interactive, output_name, debug):
    """
    Generates ssp.yaml file. By default, basic mode is invoked, setting few basic options. For more optimal experience, run ssp generate in interactive mode, via `ssp generate -i`
    """
    launcher = ssp_module.SSP_Launcher(debug=debug, require_yaml_exists=False)

    try:
        os.environ.pop('SSP_CONFIG_NAME')
        os.environ.pop('SSP_CONFIG_PATH')
    except KeyError:
        logging.debug("Keys not set, continuing...")

    setup_docker_url = config.SSP_DOCKER_URL
    setup_docker_name = config.SSP_IMAGE_NAME

    output = f"ssp_generated{round(time.time())}.yaml" if not output_name else output_name
    if output[-5:] != '.yaml':
        output += '.yaml'

    if interactive:
        yaml_path, yaml_name = _setup_interactive(
            setup_docker_url, setup_docker_name, launcher, output)
    else:
        yaml_path, yaml_name = _setup_basic(
            setup_docker_url, setup_docker_name, launcher, output)

    if not output_name and click.confirm(f"Do you want to rename {yaml_name} to {config.SSP_CONFIG_NAME}?"):
        os.rename(yaml_path.joinpath(yaml_name),
                  pathlib.Path().cwd().joinpath(config.SSP_CONFIG_NAME))
        logging.info("Successfully renamed %s to %s" %
                     (pathlib.Path(yaml_path, yaml_name), pathlib.Path().cwd().joinpath(config.SSP_CONFIG_NAME)))
    if not interactive:
        logging.info(
            "For more advanced SSP yaml configuration, try `ssp generate -i`")


def _setup_basic(setup_docker_url, setup_docker_name, launcher, output):
    logging.info("Starting basic setup...")

    logging.info("Docker url is: %s" % setup_docker_url)
    logging.info("Docker url is: %s" % setup_docker_name)

    setup_users = set()
    default_id = 1001
    user = User()
    user.id = default_id
    logging.info("Default user id set to: %s" % user.id)
    user.gid = default_id
    logging.info("Default usergroup id set to: %s" % user.gid)
    user.name = launcher.current_user
    logging.info("Default username set to: %s" % user.name)
    user.shell = '/bin/bash'
    logging.info("Default shell set to: %s" % user.shell)
    setup_users.add(user)

    logging.info("Generating yaml file...")
    yaml_path, yaml_name = launcher.setup(output, setup_docker_url=setup_docker_url,
                                          setup_docker_name=setup_docker_name,
                                          setup_users=setup_users)

    logging.info("Generated SSP configuration file: %s to %s" %
                 (yaml_name, yaml_path))

    return yaml_path, yaml_name


def _setup_interactive(setup_docker_url, setup_docker_name, launcher, output):
    setup_docker_url = click.prompt(
        "Enter URL of SSP docker image", default=setup_docker_url, type=str)

    setup_docker_name = click.prompt(
        "Enter name for new docker image", default=setup_docker_name, type=str)
    click.echo("")

    setup_groups = set()
    if click.confirm("Do you want to define user groups?"):
        setup_groups = set(_generic_prompt(
            "Please, enter a unique group name", "", str,
            "Please, enter a unique group id", 1234, int,
            "Incorrectly filled-in groups setup"
        ))
    click.echo("")

    # Groups have to be defined before users definition
    setup_users = set()
    default_id = 1001
    first_user = True
    while True:
        user = User()

        if first_user:
            user.name = launcher.current_user
            first_user = False
        else:
            user.name = click.prompt(
                "Enter Name for this user", default="", type=str)

        user.uid = click.prompt(
            "Enter UID for %s" % user.name, default=default_id, type=int)
        user.gid = click.prompt(
            "Enter GID for %s" % user.name, default=default_id, type=int)

        if user.uid in [map(lambda x: getattr(x, 'uid'), setup_users)]:
            logging.error(
                "Unable to create user %s as this uid is already taken." % user.name)
            continue

        user.shell = click.prompt(
            "Which shell should be used by %s" % user.name, default='/bin/bash', type=str)

        if len(setup_groups) > 0:
            user.groups = inquirer.prompt([inquirer.Checkbox('selected_groups',
                                                             message="Select which groups you want user %s be part of" % user.name,
                                                             choices=[group for group in setup_groups])])['selected_groups']

        setup_users.add(user)
        if not click.confirm("Do you want to define more users?"):
            break
        default_id += 1
    click.echo("")

    setup_drives = set()
    if click.confirm("Do you want to mount external drives?"):
        setup_drives = set(_generic_prompt(
            "Please, enter mount source [server.address:/source/location]", "", str,
            "Please, enter mount location [/target/location]", "", str,
            "Incorrectly filled-in mount command"
        ))
    click.echo("")

    setup_symlinks = set()
    if click.confirm("Do you want to create symlinks?"):
        setup_symlinks = set(_generic_prompt(
            "Please, enter symlink source [/path/to/source]", "", str,
            "Please, enter symlink target [/path/to/target]", "", str,
            "Incorrectly filled-in symlinks"
        ))
    click.echo("")

    setup_copyfiles = set()
    if click.confirm("Do you want to copy files from host to ssp docker container?"):
        setup_copyfiles = set(_generic_prompt(
            "Please, enter host source path to file [/path/to/source]", "", str,
            "Please, enter docker image target path to file [/path/to/target]", "", str,
            "Incorrectly filled-in groups setup", check_file_exists=True
        ))

    click.echo("")

    setup_env_vars = set()
    if click.confirm("Do you want to define environment variables?"):
        if click.confirm("Do you want to enter environment variables from file?"):
            while True:
                envvar_path = click.prompt(
                    "Enter path to file contating environment variables", type=pathlib.Path)
                try:
                    open(envvar_path, 'r')
                except FileNotFoundError:
                    logging.error("File %s not found, try again!" %
                                  envvar_path)
                    continue
                break
            setup_env_vars = set(launcher.read_envvar_file(envvar_path))
            logging.debug(setup_env_vars)
        else:
            while True:
                entry = click.prompt(
                    "Please enter env. variable (leavy empty to continue)", default="")
                if entry == "":
                    break
                setup_env_vars.add(entry)

    click.echo("")

    yaml_path, yaml_name = launcher.setup(output, setup_docker_url=setup_docker_url, setup_docker_name=setup_docker_name,
                                          setup_groups=setup_groups,  setup_users=setup_users,
                                          setup_symlinks=setup_symlinks, setup_drives=setup_drives,
                                          setup_copyfiles=setup_copyfiles, setup_env_vars=setup_env_vars)

    logging.info("Generated SSP configuration file: %s to %s" %
                 (yaml_name, yaml_path))

    return yaml_path, yaml_name


@ssp.command()
@click.option('-x', '-X', 'sshx', is_flag=True, help="Launches docker in detached mode and connets to docker via ssh with xserver.")
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, help="Creates only Dockerfile.")
@click.option('-f', '--from-file', is_flag=True, help="Building Dockerfile will be skipped, using dockerfile in current folder.")
@click.option('--skip-config', is_flag=True, help="During cpm init, doesnt ask to configure each package and skips all questions.")
@click.option('--debug', is_flag=True)
def run(sshx, dry_run, from_file, skip_config, debug):
    """
    Run ssp via this command. SSP needs ssp.yaml configuration file in order tu run. To generate this file, run `ssp generate`
    """
    if from_file:
        launcher = ssp_module.SSP_Launcher(
            debug=debug, require_yaml_exists=False)
        launcher.run_from_file(sshx)
    else:
        launcher = ssp_module.SSP_Launcher(debug=debug)
        launcher.run(sshx, dry_run, skip_config)


@ssp.command()
def version():
    click.echo(ssp_base.__version__, nl=True)


def _generic_prompt(first_message="First input", first_default="", first_type=str,
                    second_message="Second input", second_default="", second_type=str,
                    error_message="Error occured. Skipping...",  skip_second=False, check_file_exists=False):
    while True:
        prompt_first = click.prompt(
            first_message + " (leavy empty to continue)", default=first_default, type=first_type)
        if check_file_exists and not pathlib.Path(prompt_first).exists():
            logging.error(
                "Selected source file does not exist: %s " % prompt_first)
            continue

        if len(str(prompt_first)) < 1:
            break

        prompt_second = "skipped..."
        if not skip_second:
            prompt_second = click.prompt(
                second_message, default=second_default, type=second_type)

        # if prompt_group_name InterruptedError
        if len(str(prompt_first)) < 1:
            logging.error(error_message)
        else:
            yield (prompt_first, prompt_second)
        logging.debug("Prompt filled: %s %s" % (prompt_first, prompt_second))
