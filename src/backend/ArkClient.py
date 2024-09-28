# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import requests, zipfile
from io import BytesIO
from ..backend import ArkClientPayload as acp
from ..utils.AnalyUtils import TestRT


class ArkClientRequestError(OSError):
    def __init__(self, *args:object):
        super().__init__(*args)


class ArkClientStateError(RuntimeError):
    def __init__(self, *args:object):
        super().__init__(*args)


class ArkClient:
    """Arknights C/S communication handler."""
    DEFAULT_DEVICE = 'Android'
    CONN_TIMEOUT = 10

    def __init__(self, device:str=DEFAULT_DEVICE):
        """Initializes an ArkClient instance.

        :param device: The device tag of the client;
        """
        self._session:requests.Session = requests.Session()
        self._version:acp.ArkVersion = None
        self._config:acp.ArkNetworkConfig = None
        self._device:str = device

    def _fetch_bytes(self, url:str):
        try:
            rsp = self._session.get(url, timeout=ArkClient.CONN_TIMEOUT)
            if rsp.status_code == 200:
                return bytes(rsp.content)
            else:
                raise ArkClientRequestError(f"{rsp.status_code}: {url}")
        except requests.RequestException as arg:
            raise ArkClientRequestError(f"Failed to GET binary content: {url}") from arg

    def _fetch_dict(self, url:str):
        try:
            rsp = self._session.get(url, timeout=ArkClient.CONN_TIMEOUT)
            if rsp.status_code == 200:
                return dict(rsp.json())
            else:
                raise ArkClientRequestError(f"{rsp.status_code}: {url}")
        except requests.RequestException as arg:
            raise ArkClientRequestError(f"Failed to GET JSON content: {url}") from arg

    def get_remote_network_config(self):
        """Fetches the network config from the remote."""
        return acp.ArkNetworkConfig(self._fetch_dict(acp.ArkNetworkConfig.SOURCE))

    def get_remote_version(self):
        """Fetches the version info from the remote."""
        if self._config is None:
            raise ArkClientStateError("Network config is not initialized yet")
        return acp.ArkVersion(self._fetch_dict(self._config.api_version(self._device)))

    def get_asset(self, name:str, unzip:bool=False):
        """Fetches a hot-update asset from the remote. Returns its file-like object.

        :param name: The name of the asset;
        :param unzip: Whether to return the unzipped data;
        """
        if self._config is None:
            raise ArkClientStateError("Network config is not initialized yet")
        if self._version is None:
            raise ArkClientStateError("Version is not initialized yet")
        data = self._fetch_bytes(
            f"{self._config.get('hu')}/{self._device}/assets/{self._version.res}/{name}")
        if unzip:
            with TestRT('client_unzip_mem'):
                with zipfile.ZipFile(BytesIO(data)) as zf:
                    nl = zf.namelist()
                    if len(nl) != 1:
                        raise ArkClientStateError("Zipfile contains unexpected entry length")
                    return zf.open(nl[0]).read()
        else:
            return data

    def get_repo(self):
        """Fetches the remote asset repository info from the remote."""
        if self._config is None:
            raise ArkClientStateError("Network config is not initialized yet")
        if self._version is None:
            raise ArkClientStateError("Version is not initialized yet")
        return acp.ArkRemoteAssetsRepo(self._fetch_dict(
            f"{self._config.get('hu')}/{self._device}/assets/{self._version.res}/hot_update_list.json"))

    def set_current_network_config(self, config:acp.ArkNetworkConfig=None):
        """Sets the network config of the client.

        :param config: The network config. If `None`, an fetching from the remote will be performed;
        """
        if config is None:
            config = self.get_remote_network_config()
        self._config = config

    def set_current_version(self, version:acp.ArkVersion=None):
        """Sets the version info of the client.

        :param version: The new version. If `None`, an fetching from the remote will be performed;
        """
        if version is None:
            version = self.get_remote_version()
        self._version = version
