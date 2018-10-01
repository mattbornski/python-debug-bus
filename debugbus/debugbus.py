import collections
import json
import redis
import threading
import uuid

class Client(object):
    def __init__(self, redis_url_source='redis://127.0.0.1:6379?db=0'):
        self._redis_url = None
        self._redis_client = None
        self._redis_url_source = redis_url_source
        self._callbacks = collections.defaultdict(lambda: [])

    def get_redis_url(self):
        if self._redis_url is None:
            try:
                self._redis_url = self._redis_url_source()
            except TypeError:
                pass

        if self._redis_url is None:
            self._redis_url = self._redis_url_source

        return self._redis_url

    @property
    def redis_client(self):
        try:
            if self._redis_client is not None:
                return self._redis_client
        except AttributeError:
            pass

        self._redis_url = self.get_redis_url()
        connection_pool = redis.ConnectionPool.from_url(self._redis_url)

        client_kwargs = {
            'decode_responses': True,
            'connection_pool': connection_pool,
        }

        self._redis_client = redis.StrictRedis(**client_kwargs)
        return self._redis_client

    def disconnect(self):
        if self._redis_client is not None:
            self._redis_url = None
            self._redis_client = None

        for callback in self._callbacks['disconnect']:
            callback()

    def record(self, event_name, **kwargs):
        event_uuid = kwargs.get('event_uuid', None) or str(uuid.uuid4())
        event = {
            'event_name': event_name,
            'event_uuid': event_uuid,
        }

        try:
            result = self.redis_client.publish('default', json.dumps(event))
        except redis.exceptions.ConnectionError as e:
            self.disconnect()

    def on_message(self, callback, **kwargs):
        gate = threading.Lock()
        gate.acquire()
        def _callback():
            while True:
                pubsub = self.redis_client.pubsub()
                try:
                    pubsub.subscribe('default')
                except (OSError, redis.exceptions.ConnectionError):
                    self.disconnect()
                    continue
                
                subscribed = pubsub.listen()
                gate.release()
                try:
                    for message in subscribed:
                        if message['type'] == 'message':
                            callback(json.loads(message['data']))
                except (OSError, redis.exceptions.ConnectionError):
                    self.disconnect()
        t = threading.Thread(target=_callback)
        t.setDaemon(True)
        t.start()
        # Do not return until the subscription is in place
        gate.acquire()

    def on_disconnect(self, callback, **kwargs):
        self._callbacks['disconnect'].append(callback)
