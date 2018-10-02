import abc
import boto3
import contextlib
import debugbus
import json
import os
import redis
import time

class BaseSentinel(object):
    def __init__(self, config, backend):
        self._configuration = config
        self._backend = backend
    
    @abc.abstractmethod
    def setup(self):
        pass

    @abc.abstractmethod
    def takedown(self):
        pass

    @abc.abstractmethod
    def read(self):
        pass

# Most useful when paired with a web server and ngrok or similar, IMO
class FileSystemSentinel(BaseSentinel):
    pass

class RedisSentinel(BaseSentinel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        connection_pool = redis.ConnectionPool.from_url(self._backend.url)
        client_kwargs = {
            'decode_responses': True,
            'connection_pool': connection_pool,
        }
        self._redis_client = redis.StrictRedis(**client_kwargs)

    def setup(self):
        self._score = time.time()
        self._redis_client.hset(self._configuration['key'], self._score, self._backend.url)

    def takedown(self):
        self._redis_client.hdel(self._configuration['key'], self._score)

    def read(self):
        values = self._redis_client.hkeys(self._configuration['key'])
        if len(values) == 0:
            return None
        max_value = max([float(value) for value in values])
        return self._redis_client.hget(self._configuration['key'], max_value).decode('utf-8')

class SSMSentinel(BaseSentinel):
    pass

class LambdaEnvSentinel(BaseSentinel):
    pass



SENTINEL_TYPES = {
    'file': FileSystemSentinel,
    'redis': RedisSentinel,
    'ssm': SSMSentinel,
    'lambda_env': LambdaEnvSentinel,
}



def setup_sentinel(config, backend):
    klass = SENTINEL_TYPES.get(config['type'], None)
    if klass is not None:
        s = klass(config, backend)
        s.setup()
        return s
