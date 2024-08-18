# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import threading
import tkinter as tk


class GUITaskBase():
    """GUI task handler base class."""

    DEFAULT_START_MESSAGE = "正在初始化"
    DEFAULT_SUCCESS_MESSAGE = "完成"
    DEFAULT_FAILURE_MESSAGE = "失败"

    def __init__(self):
        self._completed = False
        self._cancelled = False
        self._running = False
        self._exception = None
        self.__progress = tk.DoubleVar(value=0.0)
        self.__message = tk.StringVar(value="")
        self.__thread = None

    def _run(self):
        """The main execution of the task. Must be implemented."""
        raise NotImplementedError()

    def _on_succeed(self):
        """The callback that will be called when the task succeed."""

    def _on_fail(self):
        """The callback that will be called when the task fail."""
        raise self.get_exception()

    def _on_complete(self):
        """The callback that will be called when the task succeed or fail.
        This callback will be called after `on_success` and `on_failure`.
        """

    def start(self):
        """Starts the task. It must be called at most once."""
        if self._completed:
            raise RuntimeError("This task has completed")
        if self._running:
            raise RuntimeError("This task is running now")
        def target():
            self._completed = False
            self._cancelled = False
            self._running = True
            try:
                self.__progress.set(0.0)
                self.__message.set(GUITaskBase.DEFAULT_START_MESSAGE)
                self._run()
                self.__progress.set(1.0)
                self.__message.set(GUITaskBase.DEFAULT_SUCCESS_MESSAGE)
                self._on_succeed()
            except BaseException as arg:
                self._exception = arg
                self.__message.set(GUITaskBase.DEFAULT_FAILURE_MESSAGE)
                self._on_fail()
            finally:
                self._completed = True
                self._running = False
                self._on_complete()
        self.__thread = threading.Thread(target=target, daemon=True, name=f"GUITask:{self.__class__.__name__}")
        self.__thread.start()

    def cancel(self):
        """Cancels the task. It will only sets the status to cancelled."""
        self._cancelled = True

    def update(self, progress:float=None, message:str=None):
        """Updates the progress variable or the message variable. `None` for not updated."""
        if progress:
            self.__progress.set(progress)
        if message:
            self.__message.set(message)

    def is_completed(self):
        """Returns `True` if the task was succeeded or failed."""
        return self._completed

    def is_cancelled(self):
        """Returns `True` if the task was cancelled."""
        return self._cancelled

    def is_failed(self):
        """Returns `True` if the task was failed."""
        return self._exception is not None

    def is_running(self):
        """Returns `True` if the task is running."""
        return self._running

    def get_exception(self):
        """Returns the exception that cause the failure, or `None` if no exception occurred."""
        return self._exception

    @property
    def observable_progress(self):
        """The progress variable that in [0.0, 1.0]."""
        return self.__progress

    @property
    def observable_message(self):
        """The message variable that may be displayed to the user."""
        return self.__message
