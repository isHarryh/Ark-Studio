# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License
import threading
import tkinter as tk


class GUITaskBase():
    """GUI task handler base class."""

    DEFAULT_START_MESSAGE = "正在初始化"
    DEFAULT_SUCCESS_MESSAGE = "完成"
    DEFAULT_FAILURE_MESSAGE = "失败"

    def __init__(self, title:str=""):
        self._title = title
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
            raise TaskReuseError("This task has completed")
        if self._running:
            raise TaskReuseError("This task is running now")
        GUITaskCoordinator.add_task(self)
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
                GUITaskCoordinator.remove_task(self)
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
    def title(self):
        """The title of the task."""
        return self._title

    @property
    def observable_progress(self):
        """The progress variable that in [0.0, 1.0]."""
        return self.__progress

    @property
    def observable_message(self):
        """The message variable that may be displayed to the user."""
        return self.__message


class GUITaskCoordinator():
    _REGISTRY:"dict[type[GUITaskBase],tuple[tk.BooleanVar,list[type[GUITaskBase]]]]" = {
        # (type) Task class : (BooleanVar) Unblocked indicator, (list) Blocking task classes
    }
    _REGISTRY_LOCK = threading.Lock()

    _RUNNING:"list[GUITaskBase]" = [
        # (GuiTaskBase, ...) Currently running tasks
    ]
    _RUNNING_LOCK = threading.Lock()

    @staticmethod
    def register(task_cls:"type[GUITaskBase]", blocking_tasks_cls:"list[type[GUITaskBase]]"):
        """Registers a new task class."""
        with GUITaskCoordinator._REGISTRY_LOCK:
            if task_cls in GUITaskCoordinator._REGISTRY:
                raise TaskCoordinatorError("Duplicated registry entry")
            bool_var = tk.BooleanVar(value=True)
            GUITaskCoordinator._REGISTRY[task_cls] = (bool_var, blocking_tasks_cls)

    @staticmethod
    def get_unblocked_indicator(task_cls:"type[GUITaskBase]"):
        """Gets the unblocked indicator of the given task class."""
        with GUITaskCoordinator._REGISTRY_LOCK:
            if task_cls not in GUITaskCoordinator._REGISTRY:
                raise TaskCoordinatorError(f"{task_cls} has not been registered yet")
            return GUITaskCoordinator._REGISTRY[task_cls][0]

    @staticmethod
    def add_task(new_task:GUITaskBase):
        """Adds a new task instance. Error will be raised if blocking triggered."""
        with GUITaskCoordinator._RUNNING_LOCK:
            if any(new_task == t for t in GUITaskCoordinator._RUNNING):
                raise TaskReuseError(f"This task already exists")
            if not GUITaskCoordinator.get_unblocked_indicator(new_task.__class__).get():
                raise TaskBlockingError(f"{new_task.__class__} cannot run due to blocking rule")
            GUITaskCoordinator._RUNNING.append(new_task)
            GUITaskCoordinator._update_vars()

    @staticmethod
    def remove_task(old_task:GUITaskBase):
        """Removes an old task instance."""
        with GUITaskCoordinator._RUNNING_LOCK:
            if old_task not in GUITaskCoordinator._RUNNING:
                return
            GUITaskCoordinator._RUNNING.remove(old_task)
            GUITaskCoordinator._update_vars()

    @staticmethod
    def _update_vars():
        with GUITaskCoordinator._REGISTRY_LOCK:
            for _, (bool_var, blocking_tasks_cls) in GUITaskCoordinator._REGISTRY.items():
                bool_var.set(
                    all(
                        all(
                            not isinstance(t, r)
                            for r in blocking_tasks_cls
                        )
                        for t in GUITaskCoordinator._RUNNING
                    )
                )


class TaskReuseError(RuntimeError):
    def __init__(self, *args:object):
        super().__init__(*args)


class TaskBlockingError(RuntimeError):
    def __init__(self, *args:object):
        super().__init__(*args)


class TaskCoordinatorError(RuntimeError):
    def __init__(self, *args:object):
        super().__init__(*args)
