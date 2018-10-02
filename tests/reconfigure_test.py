import atexit
import inspect
import os
import socket
import sys
import threading
import time
import uuid

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
src_dir = os.path.abspath(os.path.join(test_dir, '..', 'debugbus'))
sys.path.append(src_dir)

import debugbus

def forward(lock, source, destination):
    string = ''
    source.settimeout(2.0)
    while not lock.locked():
        try:
            string = source.recv(1024)
            if len(string) == 0:
                break
        except socket.timeout:
            continue
        destination.sendall(string)
    try:
        source.shutdown(socket.SHUT_RD)
    except OSError:
        pass
    try:
        destination.shutdown(socket.SHUT_WR)
    except OSError:
        pass

class ForwardingServer(object):
    def __init__(self, port=None):
        self._port_lock = threading.Lock()
        self._port = port
        self._thread = None
        self._shutdown = threading.Lock()
        self._shutdown.acquire()

    @property
    def port(self):
        if self._port is None:
            self._port_lock.acquire()
            try:
                assert self._port is None
                s = socket.socket()
                s.bind(('', 0))
                self._port = s.getsockname()[1]
                s.close()
            except AssertionError:
                pass
            finally:
                self._port_lock.release()
        return self._port

    def serve(self):
        gate = threading.Lock()
        gate.acquire()
        def _serve():
            accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            accept_socket.bind(('', self.port))
            accept_socket.listen(5)
            accept_socket.settimeout(2.0)
            self._shutdown.release()
            gate.release()
            while not self._shutdown.locked():
                try:
                    client_socket = accept_socket.accept()[0]
                except socket.timeout:
                    continue
                if self._shutdown.locked():
                    break
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect(('127.0.0.1', 6379))
                for args in [
                    (self._shutdown, client_socket, server_socket),
                    (self._shutdown, server_socket, client_socket),
                ]:
                    t = threading.Thread(target=forward, args=args)
                    t.setDaemon(True)
                    t.start()

        atexit.register(self.shutdown)
        self._thread = threading.Thread(target=_serve)
        self._thread.setDaemon(True)
        self._thread.start()
        # Wait for server to start before returning
        gate.acquire()

    def shutdown(self):
        if self._thread is not None:
            self._shutdown.acquire()
            self._thread.join()
            self._thread = None

def test_downed_bus():
    server = ForwardingServer()
    server.serve()
    client = debugbus.Client('redis://127.0.0.1:{}'.format(server.port))

    received = []
    def receiver(message):
        received.append(message)
    client.on_message(receiver)

    successful_event_name = str(uuid.uuid4())
    client.record(successful_event_name)
    delay = 0
    while len(received) < 1:
        time.sleep(1)
        delay += 1

    server.shutdown()
    failed_event_name = str(uuid.uuid4())
    client.record(failed_event_name)
    time.sleep(2 * delay)

    assert len(received) == 1
    assert received[0]['event_name'] == successful_event_name
    assert received[0]['event_uuid'] is not None

def test_reconfigured_bus():
    server = ForwardingServer()
    server.serve()
    url = 'redis://127.0.0.1:{}'.format(server.port)
    def url_getter():
        return url
    client = debugbus.Client(url_getter)

    received = []
    def receiver(message):
        if received is not None:
            received.append(message)
    def disconnecter():
        received = None
    client.on_disconnect(disconnecter)
    client.on_message(receiver)

    successful_event_name_1 = str(uuid.uuid4())
    client.record(successful_event_name_1)
    delay = 0
    while len(received) < 1:
        time.sleep(1)
        delay += 1

    server.shutdown()
    failed_event_name = str(uuid.uuid4())
    client.record(failed_event_name)
    time.sleep(2 * delay)

    server = ForwardingServer()
    server.serve()
    url = 'redis://127.0.0.1:{}'.format(server.port)
    time.sleep(1)

    successful_event_name_2 = str(uuid.uuid4())
    client.record(successful_event_name_2)
    while len(received) < 2:
        time.sleep(1)

    assert len(received) == 2
    assert received[0]['event_name'] == successful_event_name_1
    assert received[0]['event_uuid'] is not None
    assert received[1]['event_name'] == successful_event_name_2
    assert received[1]['event_uuid'] is not None
