# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time
from contextlib import ContextDecorator
from collections import defaultdict


class DurationFormatter:
    @staticmethod
    def apply(sec:"int|float"):
        if not isinstance(sec, (int, float)):
            raise TypeError("Argument sec should be int or float")
        h = int(sec / 3600)
        m = int(sec % 3600 / 60)
        s = int(sec % 60)
        ms = round((sec - int(sec)) * 1000) if isinstance(sec, float) else None
        if h != 0:
            return f'{h}:{m:02}:{s:02}' + f'.{ms:03}' if isinstance(sec, float) else ''
        return f'{m:02}:{s:02}' + f'.{ms:03}' if isinstance(sec, float) else ''


class TestRT(ContextDecorator):
    """Utility class for testing the running time of a code block. Usage is shown below.

    ```
    with TestRT('scope'):
        pass # The codes to test
    print(TestRT.get_avg_time('scope'))
    ```
    """

    # 类级别的字典，用于存储每个name的运行时间
    _records = defaultdict(list)

    def __init__(self, name):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        span = time.time() - self.start_time
        TestRT._records[self.name].append(span)
        return False # Hand down the exception

    @staticmethod
    def get_avg_time(name):
        times = TestRT._records.get(name, None)
        return sum(times) / len(times) if times else None

    @staticmethod
    def get_avg_time_all():
        return {k: sum(v) / len(v) for k, v in TestRT._records.items()}
