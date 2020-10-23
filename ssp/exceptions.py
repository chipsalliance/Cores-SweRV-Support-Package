class DockerException(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(self.message)

class ConfigurationError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(self.message)
