import _zephyr as _z
import os

from _zephyr import receive, ZNotice

__inited = False

def init(session_data=None, cancel_subs=True):
    global __inited
    if not __inited:
        _z.initialize()
        if session_data:
            _z.loadSession(session_data)
        else:
            _z.openPort()
            if cancel_subs:
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
        item = [elt if isinstance(elt, bytes) else elt.encode('utf-8')
                for elt in item]

        if item[2].startswith(b'*'):
            item[2] = item[2][1:]

        if b'@' not in item[2]:
            item[2] += b'@' + _z.realm()

        return tuple(item)

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

    def discard(self, item):
        try:
            self.remove(item)
        except KeyError:
            pass

    def clear(self):
        _z.cancelSubs()
        super().clear()

    def add_default_subs(self):
        _z.subDefaults()
        self.resync()

    def resync(self):
        subs = _z.getSubscriptions()
        super().clear()
        for c_item in subs:
            item = tuple(x.decode('utf-8') for x in c_item)
            super().add(self._fixTuple(item))

    # Disable set functions that do not work with the Subscription object.
    def update(self, *_others):
        raise NotImplementedError

    def __ior__(self, other):
        raise NotImplementedError

    def intersection_update(self, *_others):
        raise NotImplementedError

    def __iand__(self, other):
        raise NotImplementedError

    def difference_update(self, *_others):
        raise NotImplementedError

    def __isub__(self, other):
        raise NotImplementedError

    def symmetric_difference_update(self, *_others):
        raise NotImplementedError

    def __ixor__(self, other):
        raise NotImplementedError

    def discard(self, _elem):
        raise NotImplementedError

    def pop(self, _elem):
        raise NotImplementedError

    @property
    def cleanup(self):
        return self._cleanup

    @cleanup.setter
    def cleanup(self, value: bool):
        self._cleanup = bool(value)
