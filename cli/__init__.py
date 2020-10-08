import click

import ssp as ssp_base

from ssp import launcher as launcher_module


@click.group()
def ssp():
    """ Codasip Launcher for SSP."""
    pass


@ssp.command()
@click.option('-v', '--version', type=str, default='latest', help="Optional. Other version tha latest can be downloaded.")
def download(version):
    launcher = launcher_module.SSP_Launcher()
    launcher.download(version)


@ssp.command()
@click.option('-x', '-X', 'sshx', is_flag=True, help="Launches docker in detached mode and connets to docker via ssh with xserver.")
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, help="Only creates Dockerfile and builds docker image.")
@click.option('--skip-config', is_flag=True, help="During cpm init, doesnt ask to configure each package and skips all questions.")
def run(sshx, dry_run, skip_config):
    launcher = launcher_module.SSP_Launcher()
    launcher.run(sshx, dry_run, skip_config)


@ssp.command()
def version():
    click.echo(ssp_base.__version__, nl=True)
