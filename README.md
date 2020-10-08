# SweRV Support Package

## Introduction

### What is SweRV

SweRV is a family of RISC-V cores developed by [Western Digital](https://www.westerndigital.com/) and open-sourced through [CHIPS Alliance](https://chipsalliance.org/). 
**EH1 SweRV RISC-V Core <sup>TM</sup>** is a high-performance embedded RISC-V processor core (RV32IMC).
**EH2 SweRV RISC-V Core <sup>TM</sup>** is based on EH1 and adds dual threaded capability.
**EL2 SweRV RISC-V Core <sup>TM</sup>** is a small, ultra-low-power core with moderate performance.
The RTL code of all SweRV cores is available free of charge on GitHub in the respective CHIPSAlliance repositories:
* [EH1](https://github.com/chipsalliance/Cores-SweRV)
* [EH2](https://github.com/chipsalliance/Cores-SweRV-EH2)
* [EL2](https://github.com/chipsalliance/Cores-SweRV-EL2)

### What is SweRV Support Package (SSP)

SweRV Support Package (SSP) is a collection of RTL code, software, tools, documentation and other resources that are needed to implement designs for SweRV-based SoCs, test them and write software that will run on such SoCs.

SSP is maintained by Codasip GmbH, who provides also professional long term support for SweRV Core Family. SSP is delivered in the form of a Docker image to ensure portability across various platforms and reliable execution of the provided tools. Step by step guide how to install and run SSP can be found in the chapter following the introduction. The initial download and start of the SSP Docker image is accomplished through a `ssp` script which is available in this repository.

If you need help, advice, or want to report a bug related to the Support Package or the SweRV cores, please refer to the respective [CHIPS Alliance repository](https://github.com/chipsalliance) and check the existing issues. If none covers your concerns, feel free to open a new one.

### What is Docker

Docker is a containerization tool that allows to execute programs in isolated environments. It uses OS-level virtualization to run specific system and application configuration in form of a container running on the host.

There are docker management utilities allowing to start/stop containers, to save and reuse customized container image etc.

The main terms related to Docker are:

* _Docker container_ -- an isolated Docker environment that can be perceived as a lightweight virtual machine. It is a running instance of Docker image. It has its own file system and processes executed in container that run in isolation from the rest of the host operating system.
* _Docker image_ -- a template used to create a Docker container.

## SSP use cases
Following use cases will be referenced in the Step by Step How to use SSP chapter.
### SweRV Core Evaluation
Typical user's requirements:
* Run “clasic” benchmarks (coremark,drystone,embench)
* Run own benchmarks
* Run own sw cases 
* Run sw on ISS or FPGA
  
There are comprehensive guides how to run desired benchmarks in pre-defined SSP environment including the code. Similarly there are sw examples and preset SDK defaults allowing to write, build, run and evtl. debug software on SweRV Core either using Instruction Set Simulator (ISS) or FPGA development board.  

Work directory for user's code and data may be kept on shared NFS rather than inside of the SSP Docker container.
### RTL Design with SweRV Core
Typical user's requirements:
* SoC examples using SweRV Core
* Run own RTL simulations using SweRV core instance(s)
* Run own RTL synthesis using SweRV core instance(s)
* Getting support in case of unexpected results or design problems
  
There are SweRV core SoC application examples including a user's guide describing how to use them. There is a set of tailored scripts allowing to build SweRV based SoC with peripherals, synthesise and simulate it. SSP part supporting free available tools is for free. Professional EDA tool integration with documentation and examples is available only as a part of the professional support service. 

SSH access with X11 tunneling as well as using of shared NFS drives allow collaborative team work in one common or more individual containers.

### SweRV Core customization
Typical user's requirements:
* SoC examples using SweRV Core
* Including own modified SweRV core in SSP tool flow
* (optional) Adding verification flow
* Run own RTL simulations using own modified SweRV core instance(s)
* Run own RTL synthesis using own modified SweRV core instance(s)
* Getting support in case of extending/restricting the core functions 
  
There are SweRV core SoC application examples including a user's guide describing how to use them which may be used for the reference. There is a set of tailored scripts allowing to build SweRV based SoC with peripherals which may be used to build more complex SoC. Professional support service offers a help while adding a RISC-V extension (e.b. B,F etc) to actual cores.

SSH access with X11 tunneling as well as using of shared NFS drives allow collaborative team work in one common or more individual containers.


## 1. Step by step SSP installation guide
1. [Install and run Docker environment on your host](#11-installing-docker)
2. [Install ssp script on your host](#12-installing-ssp-script)
3. [Prepare ssp.yaml configuration file for `ssp` script run](#13-prepare-sspyaml-configuration-file-for-ssp-script-run) 
4. [SSP run](#14-ssp-run)

### 1.1. Installing Docker

To run SSP a Docker client environment has to installed and running on your host. You can install Docker through the package manager of your Linux distribution as follows:

On Debian:

`$ sudo apt install docker-ce`

On Ubuntu

`$ sudo apt install docker.io`

On Fedora:

`$ sudo dnf install docker`

On CentOS/RHEL OS:

`$ sudo yum install docker`

Check the dockerd status:
```
$ sudo systemctl status docker
docker.service - Docker Application Container 
Loaded: loaded (/usr/lib/systemd/system/docker.service; disabled; vendor preset: disabled)
Active: active (running) since Thu 2020-09-17 09:25:07 CEST; 8h ago
.
.
```
If docker service is NOT active (running) after installation use:
```
$ sudo systemctl start docker
```
To be able to use docker as an user (without sudo) you have to create a group `docker` and add the appropriate user to it
```
$ sudo groupadd docker
$ sudo usermod -aG docker <username>
```
You have to restart the docker service or logout/login or reboot your computer to have it active. Now you can check as an user that your docker engine is running and is ready to download and run `SSP` docker image.
```
$ docker images
REPOSITORY                                                 TAG                 IMAGE ID            CREATED             SIZE
```
There are some usefull docker commands. Note that --help can be applied also for sub-commands and options
```
$docker --help
$docker run --help       # run is used to start docker container
$docker ps --help        # ps is used to find which containers are running
$docker images --help    # images is used to see available local images
$docker image --help     # image may be used to remove desired image
```
 If you want to install the most recent version of docker client please use the official guideline [Docker installation guide]. 


If you intend to run SSP Docker directly on your own workstation, no further
configuration is needed. If it is required to run Docker containers on
a different host machine over the network, please refer to the "FAQ" section below, 

[Back to 1. Step by Step SSP Installation Guide TOC](#1-step-by-step-ssp-installation-guide).

### 1.2. Installing ssp script
`ssp` script pulls actual ssp docker image from central repository or if already pulled takes local docker image, customizes it using `ssp.yaml` configuration file and launches it. Customized ssp image is stored on local host. If customized image already exists on local host it will be simply launched.

***IMPORTANT:*** Python 3.6+ is required to run ssp. Python version can be checked:
```
$python3 --version
Python 3.6.8
```

***NOTE:*** It is not mandatory to use `ssp` script to download and launch ssp docker container however it helps ssp users to automate docker image customization.  This is needed to integrate ssp container in user's specific work environment.

You have to clone this repository and run installation using python3 environment. 
```
$git clone https://github.com/Codasip/SweRV-Support-Package-free.git
$cd SweRV-Support-Package-free
# install ssp launcher to default python install dir tree
# if you prefer user based installation or do not have permissions to write to python3 installation tree, use --user option
$python3 -m pip install -r requirements.txt .
# or
$python3 -m pip install -r requirements.txt . --user
```
Add path to `ssp` launcher to your search path. In case you have done the installation using --user, the path to the `ssp` wrapper will be in your ~/.local/bin

If you are using environment modules on your host to set your python environment and have installed ssp specific modules to the common python3.6 (or later) installation path, then you need not to do anything else. If not please add path to `ssp` launcher to your search path. (If you are not familiar with environment modules, you will see how they are used in the running ssp docker container).
```bash
## for bash 
$export PATH=$PATH:<YOUR_PYTHON3.6-INSTALL-ROOT>/bin
# or if installed using --user option
$export PATH=$PATH:/home/<YOUR_USERNAME>/.local/bin/
## for csh,tcsh
setenv PATH $PATH\:<YOUR_PYTHON3.6-INSTALL-ROOT>/bin
# or if installed using --user option
setenv PATH $PATH\:<YOUR_USERNAME>/.local/bin/
```
Now you can check `ssp` script and list its command options:
```
$ ssp --help
Usage: ssp [OPTIONS] COMMAND [ARGS]...

  Codasip Launcher for SSP.

Options:
  --help  Show this message and exit.

Commands:
  download
  run
  version
```
```
$ ssp run --help
Usage: ssp run [OPTIONS]

Options:
  -x, -X         Launches docker in detached mode and connets to docker via
                 ssh with xserver.

  -d, --dry-run  Only creates Dockerfile and builds docker image.
  --skip-config  During cpm init, doesnt ask to configure each package and
                 skips all questions.

  --help         Show this message and exit.
```

[Back to 1. Step by Step SSP Installation Guide TOC](#1-step-by-step-ssp-installation-guide).

### 1.3. Prepare ssp.yaml configuration file for `ssp` script run
`ssp.yaml` file is used by `ssp` script to generate and launch customized ssp docker image. There is an empty `ssp.yaml` file template containing brief description of each item type. Note, that you can have a several ssp.yaml configuration files to generate and run different variants of customized ssp container.
All the parameters used in ssp.yaml are well known from the Unix world however there are 2 important notes. 

* `ssp run` builds docker image and starts it by defaults with your user login. It means you have to add yourself to ssp.yaml file unless you want to use only the `--dry-run` option. 
* besides of user's specific environment variables in section *exports* you may set also optional SSP environment variables which helps to automate SSP initialization process. 
#### SSP users definition
There is a keyword `users:` denoting user definition section. You can define here all users which are intended to use this customized SSP docker container.

***IMPORTANT*** You have to define at least your actual user name in ssp.yaml. Otherwise `ssp run` will exit complaining that your user name is not on the list of user names. Remember `ssp run` starts at the end the customized ssp with your login name. Therefore both of the names in ssp.yaml and your login name shall match.
``` 
users:   
    - name: myuser
      uid: 2998
      gid: 4001
      groups:
        - 4000
        - 2000
        - 18
        - 20
      shell: /bin/bash

```
`name:` denotes login name <br />
`uid:`  is user ID <br />
`gid:`  is primary group ID <br />
`groups:` user's group membership (e.g. dialout group to use USB interface) <br />
`shell:` terminal shell selection (bash,sh,ksh,csh,tcsh)

**NOTE:**
  * SSP setup uses by default .bashrc. In case you select another shell you have to adapt appropriate rc file accordingly to initialize e.g. environment modules.
  * ssp run starts SSP docker container with user's login. Therefore it is important to define all container users with their proper login names.
  * It is recommended to use NFS drives for user's work spaces within SSP docker container. Therefore it is important that all of the users have their unique UID which is when possible identical with the UID available on hosts using the same NFS drive.
  * ssp run creates user accounts with trivial passwords (identical to user names) in the customized docker image. It is recommended for each user to change his/her password after the container starts.
  * There is always default user `sspuser` (UID==1000,GID==1000) with default password `sspuser` in base SSP docker container. 
  * ***IMPORTANT*** dialout group which membership is mandatory for users who wants to access FPGA board over USB as a non-root users. Note that dialout group on CentOS is 18 but 20 on Debian machines. Therefore is a good idea to have both of groups defined to cover different hostOS/SSP installations.

#### SSP specific environment variables for EDA tool support
SSP uses *environment modules* to set environment variables and search paths to tool binaries. As SSP installation does not know which EDA or other supplementary tool are available on the host system, the information may be given in an interactive dialog during SSP initialization. The gained data are used to generate appropriate *modulefile* for each of the tools. Following environment variables may be used to bypass interactive dialog and automate SSP initialization process. Note that free tools do not need any MGEN_<toolname>_LICENSE_SERVER variable.

**EDA tool specific environment variables**
```
CPM_ALWAYS_CONFIGURE=True      # enables automatic generation of environment module files
MGEN_<toolname>_INSTALLDIR     # set path to tool installation root directory
MGEN_<toolname>_VERSION        # set tool version
MGEN_<toolname>_LICENSE_SERVER # tool specific license server port
```
**List of supported tool names**
```
<toolname>
GNU_TOOLCHAIN           # free
RISCV_GNU_TOOLCHAIN     # free
VERILATOR               # free
WHISPER                 # free   
XILINX_VIVADO           # free

ALDEC_ALINTPRO          # pro
ALDEC_RIVIERAPRO        # pro
SYNOPSYS_VERDI          # pro
SYNOPSYS_SPYGLASS       # pro
SYNOPSYS_VCS            # pro
SYNOPSYS_DC             # pro
CADENCE_XCELIUM         # pro
CADENCE_CONFORMAL       # pro
CADENCE_INCISIVE        # pro
CADENCE_GENUS           # pro
CADENCE_INDAGO          # pro
MENTOR_QUESTASIM        # pro

CODASIP_SVS             # svs


```
**Example of ssp.yaml file for SSP free installation**
```
# Source ssp docker image
from_image: ssp-docker-registry.codasip.com/free/distrib-ssp-seh1-free:3.0.5
# Target docker image
new_image: ssp-free-dev-group:3.0.5

# NFS drives mounted to /import/eda and /import/prj
drives:
    - storage.mydomain.com:/eda /import/eda
    - storage.mydomain.com:/prj /import/prj

symlinks:
    # - source target
    - /import/eda /eda
    - /import/prj/seh1 /prj/seh1

groups:
    # groupname: gid
    mygroup: 4000

users:
    # - name: username
    #   uid: uid_number
    #   gid: gid_number
    #   groups:
    #       - gid
    #       - gid
    #   shell: /shell/path
    - name: myuser
      uid: 2998
      gid: 4001
      groups:
        - 4000
        - 2000
      shell: /bin/bash
    - name: myuser2
      uid: 2999
      gid: 4002
      groups:
        - 4000
        - 2000
      shell: /bin/bash

      # Environment variables that will be exported. 
export:
    # - ENV_VARIABLE=True
    # - PROGRAM_VERSION=1.2.3
    - CPM_ALWAYS_CONFIGURE=True
    - MGEN_GNU_TOOLCHAIN_INSTALLDIR=/eda/linux/gnu/7.3.1
    - MGEN_GNU_TOOLCHAIN_VERSION=7.3.1
    - MGEN_VERILATOR_INSTALLDIR=/eda/linux/verilator/v4.024-1-g6f52208
    - MGEN_VERILATOR_VERSION=v4.024-1-g6f52208
    - MGEN_WHISPER_INSTALLDIR=/eda/linux/whisper/1.565
    - MGEN_WHISPER_VERSION=1.565
    - MGEN_RISCV_GNU_TOOLCHAIN_INSTALLDIR=/eda/linux/riscv-gnu-toolchain/32-9.2.0
    - MGEN_RISCV_GNU_TOOLCHAIN_VERSION=32-9.2.0
    - MGEN_XILINX_VIVADO_INSTALLDIR=/eda/linux/xilinx/vivado_2017.4
    - MGEN_XILINX_VIVADO_VERSION=2017.4
```

[Back to 1. Step by Step SSP Installation Guide TOC](#1-step-by-step-ssp-installation-guide).

### 1.4. SSP run
#### First SSP run
If you have successfully done all 3 previous steps you can start ssp now. You can either go to the SweRV support package free directory where is already your customized ssp.yaml file or you can set SSP_CONFIG_PATH environment variable to point to the directory containing your customized ssp.yaml and start `ssp run` in any of your work directories. 

***NOTE:*** ssp configuration file name MUST BE ssp.yaml

```bash
## for bash
$export SSP_CONFIG_PATH=<YOUR_PATH_TO_SSP_YAML>
## for csh,tcsh
setenv SSP_CONFIG_PATH <YOUR_PATH_TO_SSP_YAML>
```
There are several options how to use `ssp run`. 
* *ssp run --skip-config* <br />
  Use this run option to get ssp console withou any configured environment module for  external EDA tools - in case of `ssp free` it is `vivado` which installation is needed to run benchmarks and test examples in FPGA. You can configure environment modules within ssp later using `cpm config` command.
* *ssp run* <br /> 
  You get main docker console access. SSP container will be closed by exiting the console. Note that that running container has got no explicit ssh port allowing ssh access from other hosts. Read [2.6. Connect via SSH](#26-connect-via-ssh) section for ssh terminal access.
* *ssp run -X* <br />
  You get terminal access to SSP container running in detached mode. Docker container will be not stopped when you exit the terminal. There is an explicit ssp port for ssh access from other hosts.
* *ssp run --dry-run* <br />
  Docker file and docker image will be created, but not started.
```
$ ssp run 
```
Following actions are done during the first `ssp run`:
* source ssp image is pulled from the repository and stored on local host
* new docker file is generated from ssp.yaml
* new docker image is generated using new docker file 
* new docker container is started with your user name identity

Depending of your filesystem, network access and your computer performance it may take couple of minutes. SSP run using docker image generated from the first run is up within less than 1s.

[Back to 1. Step by Step SSP Installation Guide TOC](#1-step-by-step-ssp-installation-guide).


## 2 Using SSP with Docker client management tools
`ssp run` is used to build and run your customized docker image. This section describes some usefull commands and features which allows to:
*  [2.1. Check available docker images](#21-check-available-docker-images)
*  [2.2. Check running container status](#22-check-running-container-status)
*  [2.3. Stop/Kill running container](#23-stopkill-running-container)
*  [2.4. Run container](#24-run-container)
*  [2.5. Save your actual container as a new image](#25-save-your-actual-container-as-a-new-image)
*  [2.6. Connect via SSH](#26-connect-via-ssh)
*  [2.7. Connect using docker exec command](#27-connect-using-docker-exec-command)
*  [2.8. Start stopped docker container and attach to it](#28-start-stopped-docker-container-and-attach-to-it)
*  [2.9. Remove exited container(s)](#29-remove-exited-containers)

In some cases user needs the features which are not covered by the one-command-start flow using `ssp run` or `ssp run -X`. Following chapters contain description of typical use cases including suitable docker client commands. Note that this description does not replace full documentation of the docker client management commands ([docker command reference])
### 2.1 Check available docker images
`docker images` shows which images are available on your host
```
$ docker images
REPOSITORY              TAG                    IMAGE ID            CREATED             SIZE
ssp-free-pva            latest                 b126298f8593        4 weeks ago         4.57GB
ssp-dev-group           3.0.3                  bd012f0dbb74        7 days ago          4.79GB
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)
### 2.2. Check running container status
`docker ps -a` shows which docker `image` is running and which `container id` is used. `ports` information is used when you want to connect via `ssh` to this particular running container. `-a` shows all container including those which were exited (status Exited).
```
$ docker ps -a
  CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS            PORTS                   NAMES
60e4d14db476        ssp-free-pva          "/bin/sh -c 'sudo mo…"   2 minutes ago       Exited (0) About a minute ago               ssp_pva
8619a9bf168c        ssp-dev-group:3.0.3   "/bin/sh -c 'sudo mo…"   4 minutes ago       Up 4 minutes                                elated_cori
04fdc29b4aab        f73f33c844a1          "/bin/sh -c 'sudo mo…"   4 weeks ago         Up 4 weeks          0.0.0.0:32810->22/tcp   pv_ssp                   
``` 
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)
### 2.3. Stop/Kill running container
`docker stop <container id>` or `docker kill <container id>` kills running container. All the data or set ups done in this running container will be lost. 
```
$ docker stop 04fdc29b4aab
04fdc29b4aab

$ docker ps
  CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                   NAMES
8619a9bf168c        ssp-dev-group:3.0.3   "/bin/sh -c 'sudo mo…"   4 minutes ago       Up 4 minutes                                elated_cori   
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)
### 2.4. Run container
There are several options how to run a docker container manually without `ssp run` script. In case of SSP we recommend to use commands similar to to those from following examples:
```
# downloads and starts ssp-free in interactive terminal. When exited, no data are lost. Container can be started to continue with the work. This corresponds with "ssp run" script command.
$ docker run -it --privileged -p 22 --name ssp_my -h ssp_my ssp-docker-registry.codasip.com/distrib-ssp-seh1-free:latest

# downloads and starts ssp-free in interactive terminal. When exited container is killed and volatile data are lost.
$ docker run -it --rm --privileged -p 22 --name ssp_my -h ssp_my ssp-docker-registry.codasip.com/distrib-ssp-seh1-free:latest

# downloads and starts ssp-free in background mode. You have to connect via `ssh` or to interactive session using e.g. `docker exec -it <container id> /bin/bash` This is similar to "ssp run -X" script command.
$ docker run -d --privileged -p 22 --name ssp_my -h ssp_my ssp-docker-registry.codasip.com/distrib-ssp-seh1-free:latest
```
* -it  # interactive mode
* -d   # detached (background mode)
* --rm # kill docker when exited from the docker container shell.
* --privileged # allows access to host resources This is needed in case you want to mount external or host disk drives or access FPGA board via USB
* -p   # specifies port for ssh access. Having this option allows to connect from external host to docker container through you host mapped port

[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)
### 2.5. Save your actual container as a new image
Under some circumstances you want to save your actual container with your setups as a new image. `docker commit <container name> <new image name>` can be used to do that.
```
# get running container name
$ docker ps
  CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                   NAMES
60e4d14db476        ssp-free-pva          "/bin/sh -c 'sudo mo…"   About an hour ago   Up 56 minutes       0.0.0.0:32860->22/tcp   ssp_pva
8619a9bf168c        ssp-dev-group:3.0.3   "/bin/sh -c 'sudo mo…"   3 hours ago         Up 3 hours                                  elated_cori

# save image
$ docker commit  ssp_pva my_new_ssp_pva
sha256:40b18c1e4dbf92b79a75adf0639a81f2db516499d2ac791505228e2ff1b44b21

# check available images
$ docker images
REPOSITORY          TAG                    IMAGE ID            CREATED             SIZE
my_new_ssp_pva      latest                 40b18c1e4dbf        55 seconds ago      4.57GB
ssp-dev-group       3.0.3                  bd012f0dbb74        7 days ago          4.79GB
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)
### 2.6. Connect via SSH
To execute graphical applications (GUI programs) from SSP, you need to be connected to SSP via SSH with X11 forwarding enabled. This can be achieved using `ssp run -X` which starts docker container in detached mode, starts terminal and connects to the docker container via `ssh -X`.

In case the container is already running and you want to connect to it via `ssh -X` there are 2 scenarios. <br />
1. You are on the host where is docker container running
2. You are on another host and you can connect to the host where the docker container is running

Case 1.a. <br />
If you do not see any port when applying `docker ps` you have to identify IP address of the running container and then use it to connect. 
```
# connect from your host to docker container through IP address
# get IP address of the running docker
$ docker inspect ssp_pva | grep IPAddr
            "SecondaryIPAddresses": null,
            "IPAddress": "172.17.0.4",
                    "IPAddress": "172.17.0.4",

# connect to running container ssp_pva as sspuser or if you have already  an account there created by "ssp run" you can use it instead
$ ssh -X sspuser@172.17.0.4
The authenticity of host '172.17.0.4 (172.17.0.4)' can't be established.
ECDSA key fingerprint is SHA256:GJnzhKWM72mENiQZi1Q1px9FARsmw+J1SPqMqD4Tgh0.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '172.17.0.4' (ECDSA) to the list of known hosts.
sspuser@172.17.0.4's password:

# use sspuser as a password
[sspuser@ssp_pva ~]$
```
Case 1.b. <br />
If you see some port when applying `docker ps`, you can use simply `localhost` to connect to container ssh port mapped to local host (see `docker ps` listing). 
```bash
# on docker host - get the host port number for ssh connection
$ docker ps
CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                   NAMES
60e4d14db476        ssp-free-pva          "/bin/sh -c 'sudo mo…"   2 hours ago         Up About an hour    0.0.0.0:32860->22/tcp   ssp_pva
8619a9bf168c        ssp-dev-group:3.0.3   "/bin/sh -c 'sudo mo…"   3 hours ago         Up 3 hours                                  elated_cori

# connect from your host to docker container through localhost
ssh -X sspuser@localhost -p 32860
The authenticity of host '[pc339]:32860 ([10.2.1.181]:32860)' can't be established.
ECDSA key fingerprint is SHA256:GJnzhKWM72mENiQZi1Q1px9FARsmw+J1SPqMqD4Tgh0.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '[pc339]:32860,[10.2.1.181]:32860' (ECDSA) to the list of known hosts.

# use sspuser as a password
sspuser@pc339's password: 
Last login: Tue Sep 29 12:52:24 2020 from gateway
[sspuser@ssp_pva ~]$
```
Case 2. <br />
You can directly connect through the host running the docker container. Note that container has to be started with `-p 22` option to get the ssh port mapping.
```bash
# on docker host - get the host port number for ssh connection
$ docker ps
CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                   NAMES
60e4d14db476        ssp-free-pva          "/bin/sh -c 'sudo mo…"   2 hours ago         Up About an hour    0.0.0.0:32860->22/tcp   ssp_pva
8619a9bf168c        ssp-dev-group:3.0.3   "/bin/sh -c 'sudo mo…"   3 hours ago         Up 3 hours                                  elated_cori

# connect from your host to docker container through docker host
ssh -X sspuser@dockerhost -p 32860
The authenticity of host '[pc339]:32860 ([10.2.1.181]:32860)' can't be established.
ECDSA key fingerprint is SHA256:GJnzhKWM72mENiQZi1Q1px9FARsmw+J1SPqMqD4Tgh0.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '[pc339]:32860,[10.2.1.181]:32860' (ECDSA) to the list of known hosts.

# use sspuser as a password
sspuser@pc339's password: 
Last login: Tue Sep 29 12:52:24 2020 from gateway
[sspuser@ssp_pva ~]$
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)

#### 2.7. Connect using docker exec command
`docker exec` command can be used to extern trigger a run of an executable within docker container. It can be used e.g. to start a service, to run a script or to open docker container  shell console in your terminal. Container ID or container name is needed to do that.
```
# to get container name or ID
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                   NAMES
a49217a73fa8        56de7a1ed283        "/bin/sh -c 'sudo mo…"   18 hours ago        Up 18 hours         0.0.0.0:32772->22/tcp   ssp_305

# to open docker container shell console in your terminal
$ docker exec -it ssp_305 /bin/bash

```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)

#### 2.8. Start stopped docker container and attach to it
`docker start` command can be used to start stopped docker container. 
* -a attach STDOUT/STDERR and forward signals
* -i interactive container STDIN (terminal prompt)
```bash
# check which containers are stopped
$ docker ps -a --filter "status=exited"
CONTAINER ID        IMAGE            COMMAND                  CREATED             STATUS                      PORTS    NAMES
83163520d86f        15989fe1fa19     "/bin/sh -c 'sudo /u…"   2 months ago        Exited (137) 2 months ago            OPe_jtag_example

# start stopped docker and attach to it
$ docker start -a -i OPe_jtag_example
[sspuser@83163520d86f ~]$
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)

#### 2.9. Remove exited container(s)
`docker rm` command can be used to remove stopped (exited) containers. NOTE that if you have not started the docker container with --rm option, you can exit it and the container remains frozen in exited state. You can start it and continue to work or to remove it if it became obsoleted. It is a good idea to check time to time using `docker ps -a --filter "status=exited"` how many exited dockers are still kept.
```bash
# check which containers are stopped
$ docker ps -a --filter "status=exited"
CONTAINER ID        IMAGE            COMMAND                  CREATED             STATUS                      PORTS    NAMES
83163520d86f        15989fe1fa19     "/bin/sh -c 'sudo /u…"   2 months ago        Exited (137) 2 months ago            OPe_jtag_example

# remove exited docker
$ docker rm OPe_jtag_example
OPe_jtag_example
```
[back to 2 Using SSP with Docker client management tools](#2-using-ssp-with-docker-client-management-tools)

### 3. First steps within running SSP

We assume you are already logged in SSP either directly after running `ssp run -X` command [1.4. SSP run](#14-ssp-run) or after you have connected using ssh -X ([2.6. Connect via SSH](#26-connect-via-ssh) - recommended) or simply using docker client management tool commands ([2.7. Connect using docker exec command](#27-connect-using-docker-exec-command)).

* [3.1. Check `cpm` and packages](#31-check-cpm-and-packages)
* [3.2. Check environment modules](#32-check-environment-modules)
* [3.2.1 Configure environment modules](#321-configure-environment-modules)
* [3.3. Check ssp project tree](#33-check-ssp-project-tree)
* [3.4. Check SSP documentation](#34-check-ssp-documentation)
* [3.5. Check access permissions](#35-check-access-permissions)

#### 3.1. Check `cpm` and packages
First recommended step is to check that `cpm` (Codasip Package Manager) is here and which packages are installed. Note that you can get help also on subcommands.
```
yourlogin@ssp_305 ssp]$ cpm --help
Usage: cpm [OPTIONS] COMMAND [ARGS]...

  Codasip Package Manager for SSP.

Options:
  --help  Show this message and exit.

Commands:
  add      Install one or more packages into SSP project.
  avail    Show all available packages or edalize tools.
  check    Check diff between installed pkg and original pkg.
  clean    Remove all installed packages.
  compose  Script for build of testing or production SSP Docker image.
  config   Configure package.
  init     Initialize SSP structure and install available packages.
  list     List currently installed packages.
  purge    Clear local package cache by removing .tgz files of package(s).
  remove   Uninstall one or more packages from SSP project.
  reset    Resets changes in installed packages to former state.
  version  Print CPM version.

 yourlogin@ssp_305 ssp]$  cpm list --help 
 Usage: cpm list [OPTIONS]

  List currently installed packages.

Options:
  --old    Deprecated. Uses old method to list installed packages. Takes
           longer.

  --count  Displays number of installed packages.
  --help   Show this message and exit.

yourlogin@ssp_305 ssp]$  cpm list
eclipse-mcu-ide:2.3.2
espresso-logic:2.0.0
gnu-toolchain-config:2.0.1
infra-tools-doc:2.0.1
openocd:4.0.0
riscv-gnu-toolchain:2.0.1
seh1-verilator:2.0.1
seh1:2.2.1
seh2-verilator:2.0.2
seh2:1.0.0
sel2-verilator:2.0.1
sel2:1.2.0
swervolf-coremark:1.1.1
swervolf-demo-freertos:2.2.0
swervolf-demo-leds-uart:2.2.0
swervolf-dhrystone:1.1.1
swervolf-eh1-lib:1.1.3
swervolf-embench:2.1.0
swervolf:2.0.3
vivado-config:2.0.1
whisper-iss:3.0.0
```
[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)
#### 3.2. Check environment modules
SSP installation is using environment modules for e.g. EDA tool specific environment setup. Please check that environment modules are running and are configured properly for your installation. When you have configured your `ssp.yaml` and used `ssp run` or `ssp run -X` you will see a similar listing:
```
yourlogin@ssp_305 ssp]$ module avail
---------------------------------------------------------------------------------- /prj/ssp/modules -----------------------------------
eclipse-mcu-ide         gnu-toolchain_7.3.1     openocd                 riscv-gnu-toolchain_9.2 vivado_2017.4           whisper-iss_1.549
```
If we want to use riscv-gnu-toolchain_9.2 tools from the command line we just load an appropriate module:
```
yourlogin@ssp_305 ssp]$ riscv32-unknown-elf-gcc --version
bash: riscv32-unknown-elf-gcc: command not found

# use module to set the environment
yourlogin@ssp_305 ssp]$ module load riscv-gnu-toolchain_9.2
module riscv-gnu-toolchain: version: 9.2 host: ssp_305
# the tool is now available:
yourlogin@ssp_305 ssp]$ riscv32-unknown-elf-gcc --version
riscv32-unknown-elf-gcc (GCC) 9.2.0
Copyright (C) 2019 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# add whisper
yourlogin@ssp_305 ssp]$ module load whisper-iss_1.549
module whisper-iss: version: 1.549 host: ssp_305
yourlogin@ssp_305 ssp]$ whisper --version
Version 1.549 compiled on Aug  5 2020 at 11:53:04
No program file specified.
```
You can unload any module in a similar way. Use --help to see all available module commands.
```
yourlogin@ssp_305 ssp]$ module --help
  Modules Release 3.2.10 2012-12-21 (Copyright GNU GPL v2 1991):

  Usage: module [ switches ] [ subcommand ] [subcommand-args ]

Switches:
	-H|--help		this usage info
	-V|--version		modules version & configuration options
	-f|--force		force active dependency resolution
	-t|--terse		terse    format avail and list format
	-l|--long		long     format avail and list format
	-h|--human		readable format avail and list format
	-v|--verbose		enable  verbose messages
	-s|--silent		disable verbose messages
	-c|--create		create caches for avail and apropos
	-i|--icase		case insensitive
	-u|--userlvl <lvl>	set user level to (nov[ice],exp[ert],adv[anced])
  Available SubCommands and Args:
	+ add|load		modulefile [modulefile ...]
	+ rm|unload		modulefile [modulefile ...]
	+ switch|swap		[modulefile1] modulefile2
	+ display|show		modulefile [modulefile ...]
	+ avail			[modulefile [modulefile ...]]
	+ use [-a|--append]	dir [dir ...]
	+ unuse			dir [dir ...]
	+ update
	+ refresh
	+ purge
	+ list
	+ clear
	+ help			[modulefile [modulefile ...]]
	+ whatis		[modulefile [modulefile ...]]
	+ apropos|keyword	string
	+ initadd		modulefile [modulefile ...]
	+ initprepend		modulefile [modulefile ...]
	+ initrm		modulefile [modulefile ...]
	+ initswitch		modulefile1 modulefile2
	+ initlist
	+ initclear
```
[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)

#### 3.2.1 Configure environment modules
If you have started SSP using `ssp run --skip-config` you will need to configure module manually. First you need to know which packages are available for configuration as described in [3.1. Check `cpm` and packages](#31-check-cpm-and-packages) section. Note that you have to have <package_name>-config:\<version> to be able to configure it. 
```bash
yourlogin@ssp_305 ssp]$ module avail
------------------------------------------------------------- /prj/ssp/modules ----
eclipse-mcu-ide         openocd                 riscv-gnu-toolchain_9.2 whisper-iss_1.549

# you need to check which packages can be configured
yourlogin@ssp_305 ssp]$ cpm list
eclipse-mcu-ide:2.3.2
espresso-logic:2.0.0
.
.
swervolf:2.0.3
vivado-config:2.0.1
whisper-iss:3.0.0

# you want to configure vivado
yourlogin@ssp_305 ssp]$ cpm config vivado
config/xilinx/vivado/package.json
2020-10-05 11:01:22,098 INFO [root]: Configuring package vivado-config:2.0.1
Please set your XILINX_VIVADO FPGA synthesis installation root directory: /eda/linux/xilinx/vivado_2017.4
Please set your XILINX_VIVADO FPGA synthesis version: 2017.4
2020-10-05 11:02:55,971 INFO [root]: Generating modulefile to /prj/ssp/modules/vivado_2017.4

yourlogin@ssp_305]$ module avail
------------------------------------------------------------- /prj/ssp/modules --------
eclipse-mcu-ide   openocd    riscv-gnu-toolchain_9.2    vivado_2017.4           whisper-iss_1.549

```
***IMPORTANT*** If you have already included Vivado specific environment variables in `ssp.yaml` and started using `ssp run` your Vivado module will be already configured during the docker container start. For more details about the ssp environment variables see [SSP specific environment variables for EDA tool support](#ssp-specific-environment-variables-for-eda-tool-support) section.

[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)
#### 3.3. Check ssp project tree
To work with SSP, the SSP project tree has to exists. When you have run SSP using `ssp run` script, SSP initialization is already done and you are able to see an installed project tree.
```
yourlogin@ssp_305 ssp]$ cd /prj/ssp
yourlogin@ssp_305 ssp]$ ls
common  config  doc  infrastructure  ip  modules  package.json  soc  sw  tool
```
[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)
#### 3.4. Check SSP documentation
There is a documentation directory containing SSP documents as well as original open source ones. The number of documents may vary depending on the packages sets you have chosen to install. Evince PDF viewer included in the container may be used to open the documentation shipped with SSP. We recommend to start with demo examples and benchmarks described in [4.5. swervolf-software-demos.pdf](#45-swervolf-software-demospdf) document to get familiar with SweRV Core and SDK ([4.7. eclipse-mcu-ide.pdf](#47-eclipse-mcu-idepdf)). <br />
***IMPORTANT*** You have to be connected to ssp docker container via ssh -X to be able to run pdf reader or other programs in GUI mode
```
yourlogin@ssp_305 ssp]$ cd /prj/ssp/doc
yourlogin@ssp_305 ssp]$ ls
eclipse-mcu-ide.pdf      seh1.pdf                              seh1_SweRV core roadmap white paper.pdf  seh2-verilator.pdf             swervolf.pdf
espresso-logic.pdf       seh1_README.md                        seh1-verilator.pdf                       sel2_README.md                 swervolf-software-demos.pdf
openocd.pdf              seh1_RISC-V_SweRV_EH1_PRM.pdf         seh2_README.md                           sel2_RISC-V_SweRV_EL2_PRM.pdf  whisper-iss.pdf

yourlogin@ssp_305 ssp]$ evince swervolf-software-demos.pdf
```
[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)
#### 3.5. Check access permissions
If you have customized SSP by adding another users you may wish to modify the access permissions allowing e.g. all group members to write to SSP project tree.
```
yourlogin@ssp_305 ssp]$ cd /prj/ssp
yourlogin@ssp_305 ssp]$ chmod g+w *
```
[back to 3. First steps within running SSP](#3-first-steps-within-running-ssp)

### 4. Overview of SSP documentation
* [4.1. seh1.pdf](#41-seh1pdf)
* [4.4. swervolf.pdf](#44-swervolfpdf)
* [4.5. swervolf-software-demos.pdf](#45-swervolf-software-demospdf)
* [4.6. openocd.pdf](#46-openocdpdf)
* [4.7. eclipse-mcu-ide.pdf](#47-eclipse-mcu-idepdf)
* [4.8. whisper-iss.pdf](#48-whisper-isspdf)
* [4.9. espresso-logic.pdf](#49-espresso-logicpdf)
* [4.10. riscv-gnu-toolchain.pdf](#410-riscv-gnu-toolchainpdf)
* [4.11. seh1_README.md](#411-seh1readmemd)
* [4.12. seh1_RISC-V_SweRV_EH1_PRM.pdf](#412-seh1risc-vswerveh1prmpdf)
* [4.14. seh1_SweRV_CoreMark_Benchmarking.pdf](#414-seh1swervcoremarkbenchmarkingpdf)
* [4.14. seh1_SweRV core roadmap white paper.pdf](#414-seh1swerv-core-roadmap-white-paperpdf)
* [4.15. seh1-verilator.pdf](#415-seh1-verilatorpdf)
* [4.16. seh2_README.md](#416-seh2readmemd)
* [4.17. seh2_RISC-V_SweRV_EH2_PRM.pdf](#417-seh2risc-vswerveh2prmpdf)
* [4.18. seh2-verilator.pdf](#418-seh2-verilatorpdf)
* [4.19. sel2_README.md](#419-sel2readmemd)
* [4.20. sel2_RISC-V_SweRV_EL2_PRM.pdf](#420-sel2risc-vswervel2prmpdf)
* [4.21. sel2-verilator.pdf](#421-sel2-verilatorpdf)
#### 4.1. seh1.pdf

This document is a modified version of the original SweRV Core<sup>TM</sup> EH1 documentation
from the release 1.8. It contains base description of SEH1 directory tree with
quick-start examples how to configure SweRV EH1 and how to run simple
"Hello world" using Verilator simulator.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)

#### 4.4. swervolf.pdf

This document is a modified version of the original SweRVolf documentation from the release 0.6.
It describes SweRVolf SoC structure, memory map and used peripherals as well as step-by-step examples
how to run simulation in `verilator` and how to run Zephyr SW application on Digilent Nexys A7
(or Nexys 4 DDR) FPGA boards.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)

#### 4.5. swervolf-software-demos.pdf

In this document, a step-by-step description is provided how to run a simple application program written in C on SweRVolf or how to run FreeRTOS-based applications on SweRVolf. This example projects can be either compiled in
command-line or in Eclipse IDE, shipped with SSP.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)

#### 4.6. openocd.pdf

This document provides deeper introduction to OpenOCD for advanced users.
A suitable version of OpenOCD with an up-to-date RISC-V support is shipped with SSP.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.7. eclipse-mcu-ide.pdf

This document describes Eclipse CDT IDE (C/C++ Development Tooling) as well as
a custom Codasip add-on (Codasip SweRV plugin) shipped with SSP.
Via the Codasip SweRV plugin, users can comfortably create new C projects
in Eclipse IDE, configured directly for SweRV EH1 or SweRVolf.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.8. whisper-iss.pdf

This document describes how to configure and use Whisper instruction set simulator (ISS)
developed by Western Digital. Whisper ISS is typically used as a golden reference
for verification of SweRV EH1. This document also shows how to run a simple workflow in Whisper ISS
in a standalone mode.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.9 espresso-logic.pdf
Brief description of boolean minimization tool which may be used to regenerate decoder Verilog description in case of adding instruction(s) to SweRV core

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.10. riscv-gnu-toolchain.pdf
Brief description of RISC-V GNU toolchain installed in SSP including the hints how to compile C program for the SweRV core.

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.11. seh1_README.md
Open source SweRV EH1 overview (code,tools)

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.12. seh1_RISC-V_SweRV_EH1_PRM.pdf
Open source SweRV EH1 programmer's manual

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.14. seh1_SweRV_CoreMark_Benchmarking.pdf
Open source SweRV EH1 benchmark results published by Western Digital

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.14. seh1_SweRV core roadmap white paper.pdf
Open source SweRV core family roadmap published by Western Digital

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.15. seh1-verilator.pdf
Open source how to run SweRV EH1 simulation in Verilator

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.16. seh2_README.md
Open source SweRV EH2 overview (code,tools)

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.17. seh2_RISC-V_SweRV_EH2_PRM.pdf
Open source SweRV EH2 programmer's manual

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.18. seh2-verilator.pdf
Open source how to run SweRV EH2 simulation in Verilator

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.19. sel2_README.md
Open source SweRV EL2 overview (code,tools)

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.20. sel2_RISC-V_SweRV_EL2_PRM.pdf
Open source SweRV EL2 programmer's manual

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
#### 4.21. sel2-verilator.pdf
Open source how to run SweRV EL2 simulation in Verilator

[back to 4. Overview of SSP documentation](#4-overview-of-ssp-documentation)
## Frequently asked questions

### Q1: I have encountered issues when running docker. The error message says "No package curl/jq available".

As of 1.1, loader requires both `curl` and `jq` packages to be installed in order to work correctly.
1. **Centos7:**  
    * `sudo yum -y update`  
    * `sudo yum -y install epel-release`  
    * `sudo yum -y install curl jq`  
  
2. **Ubuntu 14+/Debian:**  
    * `sudo apt-get update`  
    * `sudo apt-get -y install curl jq`  
  
3. **Fedora:**  
    * `sudo dnf update`  
    * `sudo dnf install curl jq`
  
### Q2: How do I configure Docker host and client for operation over network?

In case you will be running SSP on your local computer and `root` permissions are available, no further configuration of Docker is necessary.

However, if you want to make your Docker host available on your network, you will need to modify the Docker Daemon service configuration:

1. Open the service configuration file `/lib/systemd/system/docker.service`.
1. Find the key `ExecStart`.
1. Add argument:
    * `--host 0.0.0.0:2376` for encrypted communication using TLS, or
    * `--host 0.0.0.0:2375` for un-encrypted communication (not recommended).
1. Save the configuration file and restart the docker service.

Now, all clients that would like to use this machine as a Docker Host must define the environmental variable `DOCKER_HOST` so Docker can connect to the specified host.
For example, if the host's hostname is `dockerhost`, and it was configured to use TLS communication, the clients would need to run:

`$ export DOCKER_HOST=dockerhost:2376`

One can also specify host's IP address instead of hostname.

### Q3: I cannot run any graphical (GUI) applications, for instance Eclipse IDE, in the SSP. What should I do?

Running GUI applications directly in the SSP terminal is not possible as Docker container does not have any display attached. However, GUI applications can be run using the combination of SSH and X server. To enable X server within SSH connection, you need to pass the `-X` argument to the `ssh` command:

`$ ssh -X -p <forwarded_port> sspuser@localhost`

After connecting to SSP this way, you can open any graphical application and it will use the Window System of your host.

### Q4: I cannot connect to SSP via SSH, what might be the cause?

There might be multiple reasons why the SSH connection does not work properly:

1. Your firewall is blocking the connection. Try to check your firewall settings.
1. SSP container does not have the TCP port 22 forwarded from the container to the host. To forward the port, please see the [Connect via SSH](#connect-via-ssh) section in this README.
1. The port you used for the forwarding on the host may already be used by another service. Use `nmap`, `ss` or a similar utility to see the ports that are already in use.
1. There is another SSP container running on your host with the same port specified.
2. SSH daemon is not running in the SSP container. Run the command `ps aux | grep sshd` to check if the daemon is running. If you cannot see the daemon running, you can start it manually by executing `$ /usr/sbin/sshd -D &`. The reason why it is not started may be that you have overridden the startup command of the SSP container.

### Q5: Can I share my changes in SSP with other people?

Yes! Docker is prepared for these situations. There are three options how to share your SSP workspace with others.

The first option is to connect to the SSP container via SSH, so all the changes you make will be immediately available to other people connected to the same container. This option is best for sharing you workspace with colleagues.

The second way is to connect to the running container via `docker` command. However this is only possible if other people have access to the host where the docker container is running. You will need to provide them with the name of the running container that you want to share. Specifying the Docker container name is described in the _Starting SSP_ section. Then all they need to do is to run this command:

`$ docker exec -it <container_name> /bin/bash`

The third option is to export your SSP container and send it to people you want to share it with, and they import it on their side. Note that when using this approach, they will only see the changes you made to SSP before the export. To export the container, run the following commands:

```bash
# Save container as an image which can be exported, pick the <image_name> of your choice
$ docker commit <container_name> <image_name>
$ docker save --output <destination> <image_name>
```

This exports the SSP container to the `<destination>` you specify. Now you can send the generated file to anyone you choose to share the SSP content; all they need to do on their side is:

`$ docker load --input <destination>`

### Q6: How do I mount a network drive in the SSP?

To mount a network drive, you will need to install drivers for the filesystem which is used on your network drive. SSP docker already supports NFS network drives. However, to be able to mount these drives, you will need to leverage the Docker privileges, as by default the SSP container is isolated from the outer environment. To leverage the privileges, you need to start the SSP container by adding the 
`--privileged` argument to the loader script.

### Q7: I am unable to run services (daemons) in the SSP. What can I do?

Unfortunately, SSP Docker cannot run services as it does not have access to D-Bus. Any daemons you want running in the SSP must be started manually.

[Docker overview]: https://docs.docker.com/engine/docker-overview/
[Docker installation guide]: https://docs.docker.com/install/
[docker cp]: https://docs.docker.com/engine/reference/commandline/cp/
[Docker command reference]: https://docs.docker.com/engine/reference/commandline/docker/
