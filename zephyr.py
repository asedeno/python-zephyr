import _zephyr as _z
import os

from _zephyr import receive, ZNotice

__inited = False

def init(session_data=None):
    global __inited
    if not __inited:
        _z.initialize()
        if session_data:
            _z.loadSession(session_data)
        else:
            _z.openPort()
            _z.cancelSubs()
        __inited = True

class Subscriptions(set):
    """
    A set of <class, instance, recipient> tuples representing the
    tuples that have been subbed to

    Since subscriptions are shared across the entire process, this
    class is a singleton
    """
    def __new__(cls):
        if not '_instance' in cls.__dict__:
            cls._instance = super().__new__(cls)
            cls._instance._cleanup = True
            init()
        return cls._instance

    def __del__(self):
        if self._cleanup:
            _z.cancelSubs()
        try:
            super().__del__()
        except AttributeError:
            pass

    def _fixTuple(self, item):
        if len(item) != 3:
            raise TypeError('item is not a zephyr subscription tuple')

        item = list(item)
        if item[2].startswith('*'):
            item[2] = item[2][1:]

        if '@' not in item[2]:
            item[2] += f'@{_z.realm().decode("utf-8")}'

        return tuple(x.encode('utf-8') for x in item)

    def add(self, item):
        item = self._fixTuple(item)

        if item in self:
            return

        _z.sub(*item)

        super().add(item)

    def remove(self, item):
        item = self._fixTuple(item)

        if item not in self:
            raise KeyError(item)

        _z.unsub(*item)

        super().remove(item)

    @property
    def cleanup(self):
        return self._cleanup

    @cleanup.setter
    def cleanup(self, value: bool):
        self._cleanup = bool(value)
