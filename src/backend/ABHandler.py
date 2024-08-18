# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import UnityPy
from UnityPy import classes
from UnityPy.files import ObjectReader
from ..utils.AnalyUtils import TestRT


class ABHandler:

    def __init__(self, path:str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        self._path = path
        with TestRT('res_load'):
            self._env = UnityPy.load(path)
        with TestRT('res_get_objs'):
            self._objs = []
            for i in self._env.objects:
                try:
                    self.objects.append(ObjectInfo(i))
                except AttributeError:
                    pass

    @property
    def filepath(self):
        return self._path

    @property
    def objects(self):
        return self._objs


class ObjectInfo:

    def __init__(self, obj:ObjectReader):
        if obj is None:
            raise ValueError("Argument obj is None")
        self._obj:classes.GameObject = obj.read()
        if getattr(self._obj, 'type', None) is None:
            raise AttributeError("Missing type")

    ####################
    # Basic Properties #
    ####################

    @property
    def name(self):
        """Name of the object. `-` for nameless."""
        return self._obj.name if getattr(self._obj, 'name', None) else '-'

    @property
    def pathid(self):
        """Path ID property of the object."""
        return self._obj.path_id

    @property
    def type(self):
        """Class ID enumeration of the object's type."""
        return self._obj.type

    ####################
    # Asset Properties #
    ####################

    _HAS_SCRIPT = classes.TextAsset
    _HAS_IMAGE = (classes.Sprite, classes.Texture2D)
    _HAS_AUDIO = classes.AudioClip
    _EXTRACTABLE = (classes.TextAsset, classes.Sprite, classes.Texture2D, classes.AudioClip)

    def is_extractable(self):
        """Returns `True` if the object can be extracted to a file."""
        return isinstance(self._obj, ObjectInfo._EXTRACTABLE)

    @property
    def script(self):
        """Object script asset property. Returns bytes or `None` for no script. <br>
        Conventionally, only `TextAsset` objects may has script,
        which may be bytes of either decodable text or undecodable binary data.
        """
        if isinstance(self._obj, ObjectInfo._HAS_SCRIPT):
            script = bytes(self._obj.script)
            return script
        return None

    @property
    def image(self):
        """Object image asset property. Returns PIL `Image` instance or `None` for no image. <br>
        Conventionally, only `Sprite` and `Texture2D` objects may has image.
        """
        if isinstance(self._obj, ObjectInfo._HAS_IMAGE):
            image = self._obj.image
            if image.width * image.height > 0:
                return image
        return None

    @property
    def audio(self):
        """Object audio asset property. Returns `{audio_name(str): audio_data(bytes)}` or `None` for no audio. <br>
        Conventionally, only `AudioClip` objects may has audio.
        """
        if isinstance(self._obj, ObjectInfo._HAS_AUDIO):
            # TODO Access lock
            samples = self._obj.samples
            if samples:
                return {n: d for n, d in samples.items() if isinstance(n, str) and isinstance(d, bytes)}
        return None

    # TODO Detailed media info

    def __repr__(self):
        return f"GameObject({self.type.name}, {self.name})"
