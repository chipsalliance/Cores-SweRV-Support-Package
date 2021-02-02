import functools
import os
import subprocess
import sys

class Exceptions():
    class DockerException(Exception):
        def __init__(self, message, *args):
            self.message = message
            super().__init__(self.message)


    class ConfigurationError(Exception):
        def __init__(self, message, *args):
            self.message = message
            super().__init__(self.message)


    class SSPSetupError(Exception):
        def __init__(self, message, *args):
            self.message = message
            super().__init__(self.message)


    @classmethod
    def test_wrapper(cls, function):
        # Wrapper that checks if docker is installed and user has proper rights, by calling docker info
        @functools.wraps(function)
        def test_docker_installation(*args, **kwargs):
            if subprocess.run(['docker', 'info'], stdout=open(os.devnull, 'wb')).returncode != 0:
                raise Exceptions.DockerException(
                    "Docker is not properly installed.")
            return function(*args, **kwargs)
        return test_docker_installation
