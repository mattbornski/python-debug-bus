import backend
import contextlib
import debugbus
import json
import os
import sentinel



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
        return backend.RedisBackend(config)

    @contextlib.contextmanager
    def _configure_sentinels(self, backend):
        sentinels = []
        for config in self._configuration.get('sentinels', []):
            s = sentinel.setup_sentinel(config, backend)
            if s is not None:
                sentinels.append(s)

        try:
            yield
        finally:
            for s in sentinels:
                s.takedown()

    def _start_listening(self):
        client = debugbus.Client()
        def message_handler(message):
            print(message)
        client.on_message(message_handler)

    @contextlib.contextmanager
    def listen(self):
        b = self._configure_backend()
        with self._configure_sentinels(b):
            self._start_listening()
            yield



def listen():
    l = Listener()
    l.listen()
