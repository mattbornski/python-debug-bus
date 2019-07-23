import redis

class BaseBackend(object):
    def __init__(self, config):
        self._configuration = config

    @property
    def url(self):
        return self._configuration['redis_url']

    def to_json(self):
        return self._configuration

class RedisBackend(BaseBackend):
    pass
