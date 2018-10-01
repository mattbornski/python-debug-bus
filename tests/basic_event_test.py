import inspect
import os
import sys
import time
import uuid

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
src_dir = os.path.abspath(os.path.join(test_dir, '..', 'debugbus'))
sys.path.append(src_dir)

from debugbus import Client

def test_basic_events():
    client = Client()
    received = []
    event_name = str(uuid.uuid4())

    def receiver(message):
        received.append(message)
    client.on_message(receiver)
    client.record(event_name)
    while len(received) < 1:
        time.sleep(1)

    assert len(received) == 1
    assert received[0]['event_name'] == event_name
    assert received[0]['event_uuid'] is not None
