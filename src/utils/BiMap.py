# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
from typing import TypeVar, Generic


_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

class BiMap(Generic[_KT,_VT]):
    """Bi-directional mapping class."""

    def __init__(self, init_forward:"dict[_KT,_VT]"=None):
        self._forward:"dict[_KT,_VT]" = {}
        self._backward:"dict[_VT,_KT]" = {}
        if init_forward:
            for k, v in init_forward.items():
                self[k] = v

    def __setitem__(self, key:_KT, value:_VT):
        if key in self._forward:
            del self._backward[self._forward[key]]
        if value in self._backward:
            raise ValueError(f"Duplicate values are not supported: {value}")
        self._forward[key] = value
        self._backward[value] = key

    def __delitem__(self, key:_KT):
        value = self._forward.pop(key)
        del self._backward[value]

    def keys(self):
        return self._forward.keys()

    def values(self):
        return self._backward.keys()

    def get_key(self, value:_VT, default:_VT=None) -> _KT:
        return self._backward.get(value, default)

    def get_value(self, key:_KT, default:_KT=None) -> _VT:
        return self._forward.get(key, default)

    def __contains__(self, key:_KT) -> bool:
        return key in self._forward

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._forward})"
