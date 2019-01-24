from dataclasses import dataclass, field, InitVar
from threading import Thread, RLock as TRLock
from multiprocessing import Process, RLock as PRLock, Pipe
from multiprocessing.connection import Connection
from typing import Callable, Tuple, Dict


__all__ = (
    "ThreadJob",
    "ProcessJob",
    "ProcessFuture",
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


@dataclass
class ProcessFuture:
    target: InitVar[Callable]
    args: InitVar[Tuple] = tuple()
    kwargs: InitVar[Dict] = dict()
    _in_pipe: Connection = field(init=False)
    _out_pipe: Connection = field(init=False)
    _process: Process = field(init=False)

    def __post_init__(self, target, args, kwargs):
        self._out_pipe, self._in_pipe = Pipe(duplex=False)
        self._process = Process(target=self._worker, args=(target, self._in_pipe, args, kwargs))

    @staticmethod
    def _worker(target, pipe, args, kwargs):
        try:
            pipe.send(target(*args, **kwargs))
        except Exception as e:
            pipe.send(e)

    def start(self):
        self._process.start()

    def join(self):
        self._out_pipe.close()
        self._in_pipe.close()
        self._process.join()

    @property
    def done(self):
        return self._out_pipe.poll()

    @property
    def result(self):
        while not self.done:
            ...
        result = self._out_pipe.recv()
        if isinstance(result, Exception):
            raise result
        else:
            return result
