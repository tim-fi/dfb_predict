from dataclasses import dataclass, field
from threading import Thread, RLock as TRLock
from multiprocessing import Process, RLock as PRLock
from typing import Callable


__all__ = (
    "ThreadJob",
    "ProcessJob",
)


@dataclass(frozen=True)
class ThreadJob:
    target: Callable = lambda: None
    _lock: TRLock = field(default_factory=TRLock, init=False)

    def __call__(self, *args):
        if self._lock.acquire(blocking=False):
            Thread(target=self._target_wrapper, args=args).start()
            self._lock.release()

    def _target_wrapper(self, *args):
        with self._lock:
            self.target(*args)


@dataclass(frozen=True)
class ProcessJob:
    target: Callable = lambda: None
    _lock: PRLock = field(default_factory=PRLock, init=False)

    def __call__(self, *args):
        if self._lock.acquire(block=False):
            Process(target=self._target_wrapper, args=args).start()
            self._lock.release()

    def _target_wrapper(self, *args):
        with self._lock:
            self.target(*args)
