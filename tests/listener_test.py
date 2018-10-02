import inspect
import json
import os
import sys
import tempfile
import uuid

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
src_dir = os.path.abspath(os.path.join(test_dir, '..', 'debugbus'))
sys.path.append(src_dir)

import listener



def test_configuration_parsing():
    tempdir = tempfile.mkdtemp()
    with open(os.path.abspath(os.path.join(tempdir, '.debugbus.json')), 'w') as f:
        f.write(json.dumps({
            'foo': 'bar',
        }))

    original_working_dir = os.getcwd()
    try:
        os.chdir(tempdir)

        l = listener.Listener()
        assert l._configuration['foo'] == 'bar'

    finally:
        os.chdir(original_working_dir)

def test_sentinel_creation():
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

    backend = listener.RedisBackend(redis_backend_config)
    sentinel = listener.RedisSentinel(redis_sentinel_config, backend)

    l1 = listener.Listener()
    l1._configuration = {
        'backend': redis_backend_config,
        'sentinels': [redis_sentinel_config],
    }

    assert sentinel.read() is None

    with l1.listen():
        assert sentinel.read() == redis_url

    assert sentinel.read() is None
