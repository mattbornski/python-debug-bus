import inspect
import os
import sys
import uuid

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
src_dir = os.path.abspath(os.path.join(test_dir, '..', 'debugbus'))
sys.path.append(src_dir)

import backend
import listener
import sentinel



def test_redis_sentinel():
    key = str(uuid.uuid4())
    redis_url = 'redis://127.0.0.1:6379/0'
    redis_backend_config = {
        'type': 'redis',
        'redis_url': redis_url,
    }
    redis_sentinel_config = {
        'type': 'redis',
        'redis_url': redis_url,
        'key': key,
    }

    b = backend.RedisBackend(redis_backend_config)
    s = sentinel.RedisSentinel(redis_sentinel_config, b)

    assert s.read() is None

    s.setup()
    assert s.read()['redis_url'] == redis_url

    s.takedown()
    assert s.read() is None

def test_ssm_sentinel():
    key = str(uuid.uuid4())
    redis_url = 'redis://127.0.0.1:6379/0'
    redis_backend_config = {
        'type': 'redis',
        'redis_url': redis_url,
    }
    ssm_sentinel_config = {
        'type': 'ssm',
        'key': key,
    }

    b = backend.RedisBackend(redis_backend_config)
    s = sentinel.SSMSentinel(ssm_sentinel_config, b)

    assert s.read() is None

    s.setup()
    assert s.read()['redis_url'] == redis_url

    s.takedown()
    assert s.read() is None

def test_sentinel_creation_in_listener():
    key = str(uuid.uuid4())
    redis_url = 'redis://127.0.0.1:6379/0'
    redis_backend_config = {
        'type': 'redis',
        'redis_url': redis_url,
    }
    redis_sentinel_config = {
        'type': 'redis',
        'redis_url': redis_url,
        'key': key,
    }

    b = backend.RedisBackend(redis_backend_config)
    s = sentinel.RedisSentinel(redis_sentinel_config, b)

    l1 = listener.Listener()
    l1._configuration = {
        'backend': redis_backend_config,
        'sentinels': [redis_sentinel_config],
    }

    assert s.read() is None

    with l1.listen():
        assert s.read()['redis_url'] == redis_url

    assert s.read() is None
