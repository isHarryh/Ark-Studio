# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License
import requests
from datetime import datetime
from ..backend import GitHubClientPayload as ghcp


class GitHubClientRequestError(OSError):
    def __init__(self, *args:object):
        super().__init__(*args)


class GitHubClientStateError(RuntimeError):
    def __init__(self, *args:object):
        super().__init__(*args)


class GitHubClient:
    """GitHub C/S communication handler."""
    CONN_TIMEOUT = 10
    BASE_URL_REPOS = "https://api.github.com/repos"

    def __init__(self):
        self._session:requests.Session = requests.Session()

    def _fetch_list(self, url:str, params:"dict|None"=None):
        try:
            rsp = self._session.get(url, params=params, timeout=GitHubClient.CONN_TIMEOUT)
            if rsp.status_code == 200:
                return list(rsp.json())
            else:
                raise GitHubClientStateError(f"{rsp.status_code}: {url}")
        except requests.RequestException as arg:
            raise GitHubClientRequestError(f"Failed to GET JSON content: {url}") from arg

    def get_commits(
            self,
            repo:str,
            sha:"str|None"=None,
            path:"str|None"=None,
            since:"datetime|None"=None,
            until:"datetime|None"=None,
            committer:"str|None"=None,
            per_page:"int|None"=None,
            page:"int|None"=None,
        ) -> "list[ghcp.GitHubCommitData]":
        """Fetches commit history for a repository.

        :param repo: The repository in the format `owner/repo`;
        :param sha: Branch name or commit SHA (optional);
        :param path: Path to a file (optional);
        :param since: Start date for filtering commits. (optional);
        :param until: End date for filtering commits. (optional);
        :param committer: Committer username. (optional);
        :param per_page: Number of commits per page. (optional);
        :param page: Page number. (optional);
        :returns: A list of GitHubCommitData objects;
        """
        url = f"{GitHubClient.BASE_URL_REPOS}/{repo}/commits"
        params = {}

        if sha:
            params['sha'] = str(sha)
        if path:
            params['path'] = str(path)
        if since:
            params['since'] = ghcp.datetime_to_iso_utc_str(since)
        if until:
            params['until'] = ghcp.datetime_to_iso_utc_str(until)
        if committer:
            params['committer'] = str(committer)
        if per_page:
            params['per_page'] = str(per_page)
        if page:
            params['page'] = str(page)

        data = self._fetch_list(url, params=params)
        return [ghcp.GitHubCommitData.from_dict(commit) for commit in data]
