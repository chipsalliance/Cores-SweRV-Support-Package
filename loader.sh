#!/bin/bash
CONFIG_FILE='loader.cfg'

# https://stackoverflow.com/a/20816534
SCRIPTNAME="${0##*/}"
warn() {
    printf >&2 "\e[91m[ERROR]\033[0m %s: $*\n" "$SCRIPTNAME"
}

iscmd() {
    command -v >&- "$@"
}

checkdeps() {
    local -i not_found
    for cmd; do
        iscmd "$cmd" || { 
            warn $"$cmd not found"
            let not_found++
        }
    done
    (( not_found == 0 )) || {
        warn $"Install dependencies listed above to use $SCRIPTNAME"
        exit 1
    }
}
# ===

getlocation() {
   LOCATION=$(curl -s https://ipvigilante.com/"$(curl -s https://ipinfo.io/ip)" | jq .data.country_name)
   printf "\e[33m[INFO]\033[0m Your location is: %s\t" "$LOCATION"
}

# Check docker, curl and jq are installed
checkdeps curl docker jq

# Check config file exists, if yes then get docker image url - based on location
if [ -f "$CONFIG_FILE" ]; then
   getlocation
   # Uncommend line bellow if you encouter problem with using Loader from China
   # LOCATION='"China"'
   
   printf "Downloading from: %s\n" "$LOCATION"
   # shellcheck disable=SC1090
   . $CONFIG_FILE
   # shellcheck disable=SC2154
   if [ "$LOCATION" == '"China"' ]; then
      printf "\e[33m[INFO]\033[0m Using chineese repository\n"
      IMAGE_NAME="$imagecn"
   else
      printf "\e[33m[INFO]\033[0m Using worldwide repository\n"
      IMAGE_NAME="$image"
   fi
else
   printf "\e[91m[ERROR]\033[0m Configuration file %s has not been found. Cannot continue.\n" "$CONFIG_FILE"
   exit 1
fi

# Check user has access rights for docker.
docker info 1>/dev/null 2>&1
if [ "$?" -ne 0 ]; then
   printf "\e[91m[ERROR]\033[0m Docker is not properly configured. Either docker host is not properly set or you don't have required privileges. Please follow post-installation guide https://docs.docker.com/install/linux/linux-postinstall/.\033[0m\n"
   exit 1
fi

# Pull docker image.
printf "\e[33m[INFO]\033[0m Pulling \e[92m%s\033[0m\n" "$IMAGE_NAME"
docker pull "$IMAGE_NAME" || { printf "\e[91m[ERROR]\033[0m Could not pull image: %s\n" "$IMAGE_NAME"; exit 1; }


# Run image with commands from args. For more info see README.md.
printf "\e[33m[INFO]\033[0m Starting \e[92m%s\033[0m\n" "$IMAGE_NAME"
docker run "$@" "$IMAGE_NAME"
