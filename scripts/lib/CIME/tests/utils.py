import os
import tempfile
import shutil
import sys
from collections.abc import Iterable

# TODO after dropping python 2.7 replace with tempfile.TemporaryDirectory
class TemporaryDirectory(object):
    def __init__(self):
        self._tempdir = None

    def __enter__(self):
        self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def __exit__(self, *args, **kwargs):
        if os.path.exists(self._tempdir):
            shutil.rmtree(self._tempdir)

# TODO replace with actual mock once 2.7 is dropped
class Mocker:

    def __init__(self, ret=None, cmd=None, return_value=None, side_effect=None):
        self._orig = []
        self._ret = ret or return_value
        self._cmd = cmd
        self._calls = []

        if isinstance(side_effect, (list, tuple)):
            self._side_effect = iter(side_effect)
        else:
            self._side_effect = side_effect

        self._method_calls = {}

    @property
    def calls(self):
        return self._calls

    @property
    def method_calls(self):
        return dict((x, y.calls) for x, y in self._method_calls.items())

    def __getattr__(self, name):
        new_method = Mocker(self, cmd=name)
        self._method_calls[name] = new_method

        return new_method

    def __call__(self, *args, **kwargs):
        self._calls.append({"args": args, "kwargs": kwargs})

        if (self._side_effect is not None and
                isinstance(self._side_effect, Iterable)):
            rv = next(self._side_effect)
        else:
            rv = self._ret

        return rv

    def __del__(self):
        self.revert_mocks()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.revert_mocks()

    def revert_mocks(self):
        for m, module, method in self._orig:
            if isinstance(module, str):
                setattr(sys.modules[module], method, m)
            else:
                setattr(module, method, m)

    def patch(self, module, method=None, ret=None, property=False):
        if isinstance(module, str):
            x = module.split('.')
            main = '.'.join(x[:-1])
            self._orig.append((getattr(sys.modules[main], x[-1]), main, x[-1]))
            if property:
                setattr(sys.modules[main], x[-1], ret)
            else:
                setattr(sys.modules[main], x[-1], Mocker(ret, cmd=x[-1]))
        else:
            setattr(module, method, Mocker(ret))

        return ret

