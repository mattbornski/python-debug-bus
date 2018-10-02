import abc
import boto3
import contextlib
import debugbus
import json
import os
import redis
import subprocess
import time

class BaseBackend(object):
    def __init__(self, config):
        self._configuration = config

    @property
    def url(self):
        return self._configuration['redis_url']

class RedisBackend(BaseBackend):
    pass


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



class Listener(object):
    def __init__(self):
        self._listener_url = None
        self._available_technologies = set()

        self._probe_technologies()

        self._configuration = {}
        self._load_configuration()

    def _probe_technologies(self):
        # Check for ngrok / hypertunnel
        # TODO
        pass

    def _load_configuration(self):
        for path in [
            os.path.abspath(os.path.expanduser(os.path.join('~', '.debugbus', 'config.json'))),
            os.path.abspath(os.path.join('.', '.debugbus', 'config.json')),
            os.path.abspath(os.path.join('.', '.debugbus.json')),
        ]:
            try:
                with open(path, 'r') as f:
                    config = json.loads(f.read())
                    self._configuration.update(config)
            except FileNotFoundError:
                pass

    def _save_configuration(self):
        pass

    def _propose_listener_configuration(self):
        pass

    def _configure_backend(self):
        config = self._configuration.get('backend', {})
        return RedisBackend(config)

    @contextlib.contextmanager
    def _configure_sentinels(self, backend):
        sentinels = []
        for config in self._configuration.get('sentinels', []):
            sentinel = SENTINEL_TYPES.get(config['type'])(config, backend)
            sentinel.setup()
            sentinels.append(sentinel)

        try:
            yield
        finally:
            for sentinel in sentinels:
                sentinel.takedown()

    def _start_listening(self):
        client = debugbus.Client()
        def message_handler(message):
            print(message)
        client.on_message(message_handler)

    @contextlib.contextmanager
    def listen(self):
        backend = self._configure_backend()
        with self._configure_sentinels(backend):
            self._start_listening()
            yield



def listen():
    l = Listener()
    l.listen()
