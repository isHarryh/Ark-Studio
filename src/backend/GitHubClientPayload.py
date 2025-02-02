# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License
from dataclasses import dataclass
from datetime import datetime, timezone


def datetime_to_iso_utc_str(d:datetime):
    return d.astimezone(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + 'Z'


def iso_utc_str_to_datetime(s:str):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


@dataclass
class GitHubCommitData:
    """Data class to store GitHub commit information."""
    sha: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    message: str
    date: datetime
    url: str
    html_url: str

    @classmethod
    def from_dict(cls, rsp:dict):
        """Create a GitHubCommitData instance from a GitHub API response dictionary."""
        return cls(
            sha=str(rsp['sha']),
            author_name=str(rsp['commit']['author']['name']),
            author_email=str(rsp['commit']['author']['email']),
            committer_name=str(rsp['commit']['committer']['name']),
            committer_email=str(rsp['commit']['committer']['email']),
            message=str(rsp['commit']['message']),
            date=iso_utc_str_to_datetime(rsp['commit']['author']['date']),
            url=str(rsp['url']),
            html_url=str(rsp['html_url'])
        )
