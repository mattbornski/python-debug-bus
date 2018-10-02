import inspect
import json
import os
import sys
import tempfile

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
