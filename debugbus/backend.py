import redis

class BaseBackend(object):
    def __init__(self, config):
        self._configuration = config

    @property
    def url(self):
        return self._configuration['redis_url']

class RedisBackend(BaseBackend):
    pass
