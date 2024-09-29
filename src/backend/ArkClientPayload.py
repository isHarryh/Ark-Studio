# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os, re, json, hashlib
from functools import total_ordering
from collections import defaultdict

from ..utils.AnalyUtils import TestRT


CONN_TIMEOUT = 10

class ArkNetworkConfig:
    """Arknights client network config record."""

    SOURCE = "https://ak-conf.hypergryph.com/config/prod/official/network_config"
    """Response format:
    ```json
    {
        "sign": "Encoded string",
        "content": "JSON string"
    }
    ```
    """
    DEFAULT_DEVICE = 'Android'

    def __init__(self, network_config_dict:dict):
        # Retrieve config from response
        content:"dict[str,object]" = json.loads(network_config_dict.get('content'))
        configs:"dict[str,dict]" = content.get('configs')
        # Choose the first config with override=True, or the first config if none have override=True
        chosen_config = None
        for _, config in configs.items():
            if config.get('override', False):
                chosen_config = config
                break
        if not chosen_config:
            chosen_config = list(configs.values())[0]
        self._dict:"dict[str,str]" = chosen_config.get('network')

    def get(self, key:str, *args:str):
        value = self._dict.get(key, '')
        if args:
            value = value.format(*args)
        return value

    def api_version(self, device:str=DEFAULT_DEVICE):
        return self.get('hv', device)

    def api_assets(self, res_version:str, device:str=DEFAULT_DEVICE):
        return f"{self.get('hu')}/{device}/assets/{res_version}"

@total_ordering
class ArkVersion:
    """Arknights version record."""

    REG_RES_VERSION = r'\d\d-\d\d-\d\d-\d\d-\d\d-\d\d-[\da-f]{6}'

    def __init__(self, version_dict:dict=None):
        self._res:str = version_dict.get('resVersion')
        self._client:str = version_dict.get('clientVersion')

    @property
    def res(self):
        """Arknights resource version."""
        return self._res

    @property
    def client(self):
        """Arknights client version."""
        return self._client

    def _normalize_version(self, version:str):
        parts = re.split(r'[^a-zA-Z0-9]', version.lower())
        return [(0, int(char)) if char.isdigit() else (1, char) for char in parts]

    def _compare_versions(self, v1:str, v2:str):
        if v1 is None or v2 is None:
            return 0
        n1 = self._normalize_version(v1)
        n2 = self._normalize_version(v2)
        return (n1 > n2) - (n1 < n2)

    def __lt__(self, other):
        if not isinstance(other, ArkVersion):
            raise NotImplementedError()
        res_cmp = self._compare_versions(self.res, other.res)
        client_cmp = self._compare_versions(self.client, other.client)

        if res_cmp < 0 and client_cmp < 0:
            return True
        elif res_cmp >= 0 and client_cmp >= 0:
            return False
        else:
            raise ValueError("Inconsistent version comparisons")

    def __eq__(self, other):
        if not isinstance(other, ArkVersion):
            raise NotImplementedError()
        return self.res == other.res and self.client == other.client

    def __repr__(self):
        return f"Version({self._res}, {self._client})"

class AssetRepoBase:
    """Assets repository handler base class."""
    def __init__(self):
        pass

    @property
    def infos(self) -> "list[FileInfoBase]":
        raise NotImplementedError()

    def get_parent_map(self) -> "dict[FileInfoBase,FileInfoBase]":
        # Estimated RT: 0.02-0.1s (very fast)
        with TestRT('map_parent'):
            rst = {}
            for i in self.infos:
                rst[i] = i.parent
            return rst

    def get_children_map(self) -> "dict[FileInfoBase,set[FileInfoBase]]":
        # Estimated RT: 0.06~0.4s (fast)
        with TestRT('map_children'):
            rst = defaultdict(set)
            for i in self.infos:
                p, c = i.parent, i
                while p:
                    rst[p].add(c)
                    p, c = p.parent, p
            return rst

    def __repr__(self):
        return f"AssetRepo[{len(self.infos)} items]"

class ArkLocalAssetsRepo(AssetRepoBase):
    """Arknights local assets repository handler."""

    def __init__(self, root_dir:str):
        super().__init__()
        self._root_dir = root_dir
        self._infos = self._fetch_infos()

    @property
    def infos(self):
        return self._infos

    @property
    def root_dir(self):
        return self._root_dir

    def detect_res_version(self):
        for i in self.infos:
            if i.name == 'torappu_index.ab' and i.exist():
                with i.open() as f:
                    d = f.read().decode(encoding='UTF-8', errors='replace')
                    matches = re.findall(ArkVersion.REG_RES_VERSION, d)
                    if len(matches) == 1:
                        return matches[0]
                break

    def _fetch_infos(self):
        # Estimated RT: 1~2s (slow)
        with TestRT('get_infos_local'):
            if not os.path.isdir(self._root_dir):
                raise FileNotFoundError(self._root_dir)
            infos:"list[ArkLocalFileInfo]" = []
            for root, _, files in os.walk(self._root_dir):
                for f in files:
                    name = os.path.realpath(os.path.join(root, f))
                    name = os.path.relpath(name, self._root_dir)
                    name.replace('\\', '/')
                    infos.append(ArkLocalFileInfo(name, self._root_dir))
            return infos


class ArkRemoteAssetsRepo(AssetRepoBase):
    """Arknights remote assets repository handler."""

    def __init__(self, hot_update_list_dict:dict):
        super().__init__()
        # Estimated RT: 0.01-0.02s (very fast)
        with TestRT('get_infos_remote'):
            self._infos:"list[ArkRemoteFileInfo]" = \
                [ArkRemoteFileInfo(i) for i in hot_update_list_dict.get('abInfos')]
            self._packs:"list[ArkPackInfo]" = \
                [ArkPackInfo(i) for i in hot_update_list_dict.get('packInfos')]
            self._version:ArkVersion = ArkVersion({'resVersion': hot_update_list_dict.get('versionId')})

    @property
    def infos(self):
        return self._infos

    @property
    def packs(self):
        return self._packs

    @property
    def version(self):
        return self._version

class FileInfoBase:
    """File information record base class."""
    SEP = '/'
    RADIX = 1024
    UNITS = ('B', 'KB', 'MB', 'GB', 'TB')

    def __init__(self):
        self.__basename = None
        self.__parent = None

    @property
    def name(self) -> str:
        """Name. This property is the identifier and must be implemented by descendants classes."""
        raise NotImplementedError()

    @property
    def status(self) -> int:
        """Version control status. This property may be implemented by descendants classes."""
        raise NotImplementedError()

    @property
    def file_size(self) -> int:
        """File size in bytes. This property may be implemented by descendants classes."""
        raise NotImplementedError()

    @property
    def basename(self) -> str:
        """Base name. This property is lazily auto generated by the property `name`."""
        if self.__basename is None:
            chain = self.name.split(FileInfoBase.SEP)
            self.__basename = chain[-1] if len(chain) > 0 else ''
        return self.__basename

    @property
    def parent(self) -> "FileInfoBase|None":
        """Parent file info. This property is lazily auto generated by the property `name`."""
        if not self.name:
            return None
        if self.__parent is None:
            chain = self.name.split(FileInfoBase.SEP)
            self.__parent = DirFileInfo(FileInfoBase.SEP.join(chain[:-1]) if len(chain) > 1 else '')
        return self.__parent

    def get_file_size_str(self, digits:int=0):
        try:
            s = self.file_size
            for i in FileInfoBase.UNITS:
                if s > FileInfoBase.RADIX:
                    s /= FileInfoBase.RADIX
                else:
                    break
            return f"{s:.{digits}f} {i}"
        except NotImplementedError:
            return ""

    def __eq__(self, other:object):
        if isinstance(other, FileInfoBase):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"File({self.name})"

class DirFileInfo(FileInfoBase):
    """Simple implementation of directory file information record."""

    def __init__(self, name:str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def status(self):
        return FileStatus.DIRECTORY

class ArkLocalFileInfo(FileInfoBase):
    """Arknights local file information record."""

    def __init__(self, name:str, root_dir:str):
        super().__init__()
        self._name = name.replace(os.sep, '/')
        self._root_dir = root_dir
        self._path = os.path.join(self._root_dir, self._name).replace(os.sep, '/')

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def status(self):
        return FileStatus.UNCHECKED

    @property
    def md5(self):
        if os.path.isfile(self._path):
            byte = open(self._path, 'rb').read()
            return hashlib.md5(byte).hexdigest()
        return ''

    @property
    def file_size(self):
        if not os.path.isfile(self._path):
            return 0
        with open(self._path, 'rb') as f:
            return f.seek(0, os.SEEK_END)

    def exist(self):
        return os.path.isfile(self._path)

    def open(self):
        if self.exist():
            return open(self._path, 'rb')

    def delete(self):
        if self.exist():
            os.unlink(self._path)

class ArkRemoteFileInfo(FileInfoBase):
    """Arknights remote file information record."""

    def __init__(self, info_dict:dict):
        super().__init__()
        self._name:str = info_dict.get('name') # Required
        # Unused self._hash:str = info_dict.get('hash') # Required
        self._md5:str = info_dict.get('md5') # Required
        self._data_size:int = int(info_dict.get('totalSize')) # Required
        self._file_size:int = int(info_dict.get('abSize')) # Required
        # Unused self._thash:str = info_dict.get('thash', None)
        self._type:str = info_dict.get('type', None)
        self._pack:str = info_dict.get('pid', None)
        # Unused self._cid:int = info_dict.get('cid') # Required

    @property
    def name(self):
        return self._name

    @property
    def status(self):
        return FileStatus.UNCHECKED

    @property
    def md5(self):
        return self._md5

    @property
    def data_size(self):
        return self._data_size

    @property
    def file_size(self):
        return self._file_size

    @property
    def type(self):
        return self._type

    @property
    def pack(self):
        return self._pack

    @property
    def data_name(self):
        d_name = self._name.replace('/', '_').replace('#', '__')
        ext_matches = list(re.finditer(r'\..+', d_name))
        if ext_matches:
            start, end = ext_matches[-1].span()
            d_name = f'{d_name[:start]}.dat{d_name[end:]}'
        return d_name

class ArkPackInfo:
    def __init__(self, info_dict:dict):
        self._name:str = info_dict.get('name') # Required
        self._data_size:int = int(info_dict.get('totalSize')) # Required
        # Unused self._cid:int = info_dict.get('cid') # Required

    @property
    def name(self):
        return self._name

    @property
    def data_size(self):
        return self._data_size

    def __repr__(self):
        return f"Pack({self._name})"

class FileStatus:
    DIRECTORY = -1
    UNCHECKED = 0
    OKAY = 1
    ADD = 2
    ADDED = 3
    MODIFY = 4
    MODIFIED = 5
    DELETE = 6
    DELETED = 7
    _DESC = ["未检查", "无变更", "新增", "已同步新增", "修改", "已同步修改", "删除", "已同步删除"]

    @staticmethod
    def to_str(status:int):
        return FileStatus._DESC[status] if 0 <= status <= 7 else ""

class ArkIntegratedAssetRepo(AssetRepoBase):
    """Arknights integrated assets repository handler."""

    def __init__(self, local:ArkLocalAssetsRepo, remote:ArkRemoteAssetsRepo):
        super().__init__()
        self._local = local
        self._remote = remote

    @property
    def infos(self):
        # Estimated RT: 0.01-0.07s (very fast)
        with TestRT('get_infos_integrated'):
            name2local = {l.name: l for l in self._local.infos}
            name2remote = {r.name: r for r in self._remote.infos}
            infos:"list[ArkIntegratedFileInfo]" = []
            for l in self._local.infos:
                r = name2remote.get(l.name, None)
                infos.append(ArkIntegratedFileInfo(l, r))
            for r in self._remote.infos:
                if r.name not in name2local:
                    l = ArkLocalFileInfo(r.name, self._local.root_dir)
                    infos.append(ArkIntegratedFileInfo(l, r))
            return infos

    @property
    def local(self):
        return self._local

    @property
    def remote(self):
        return self._remote

class ArkIntegratedFileInfo(FileInfoBase):
    """Arknights integrated file information record."""

    def __init__(self, local:ArkLocalFileInfo, remote:ArkRemoteFileInfo=None):
        super().__init__()
        if local is None:
            raise ValueError("Argument local is none")
        if remote:
            if local.name != remote.name:
                raise ValueError("Inconsistent file name between the given local and remote")
        self._name = local.name
        self._local = local
        self._remote = remote
        self._status_cache = None

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self.local.path

    @property
    def status(self):
        self._status_cache = self.get_status()
        return self._status_cache

    @property
    def file_size(self):
        return self.remote.file_size if self.remote else self.local.file_size

    @property
    def local(self):
        return self._local

    @property
    def remote(self):
        return self._remote

    def get_status(self):
        s_local = self._local.file_size
        s_remote = self._remote.file_size if self._remote else 0
        if s_local:
            if s_local == s_remote and self._local.md5 == self._remote.md5:
                return FileStatus.MODIFIED if self._status_cache in (FileStatus.MODIFY, FileStatus.MODIFIED) else \
                    FileStatus.ADDED if self._status_cache in (FileStatus.ADD, FileStatus.ADDED) else FileStatus.OKAY
            else:
                return FileStatus.MODIFY if s_remote else FileStatus.DELETE
        else:
            return FileStatus.ADD if s_remote else FileStatus.DELETED
