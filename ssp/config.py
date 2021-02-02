import pathlib
import os

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

SSP_DOCKER_URL = "docker-registry.codasip.com/ssp/distrib-ssp-seh1-free:latest"
SSP_IMAGE_NAME = "ssp_docker_image_free:1.0.0"
# DO NOT CHANGE CODE BELLOW, MODIFY VARIABLE ABOVE ONLY
# ==============================================================================
