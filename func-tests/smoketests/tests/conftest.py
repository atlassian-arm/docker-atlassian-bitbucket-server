import logging
import os
import shutil
import time
from dataclasses import dataclass

import pytest
import requests
from requests.auth import HTTPBasicAuth


def pytest_addoption(parser):
    parser.addoption(
        "--cleanup", action="store_true", default=False, help="cleanup after tests"
    )


@dataclass
class Context:
    base_url: str
    admin_user: str
    admin_pwd: str
    indexing_timeout: int = 30 * 1000

    def __post_init__(self):
        self.admin_auth = HTTPBasicAuth(self.admin_user, self.admin_pwd)


@dataclass
class TestData:
    project_key: str
    project_name: str
    repository_name: str
    pull_request_id: str
    repo_to_clone: str
    folder: str
    new_branch: str
    user: str

    def __post_init__(self):
        self.user_auth = HTTPBasicAuth(self.user, self.user)


@pytest.fixture(scope='session')
def ctx():
    return Context(
        base_url=os.environ.get('BITBUCKET_BASE_URL', "http://bitbucket:8080"),
        admin_user=os.environ.get('BITBUCKET_ADMIN', 'admin'),
        admin_pwd=os.environ.get('BITBUCKET_ADMIN_PWD', 'admin'),
    )


@pytest.fixture(scope='session')
def tdata():
    return TestData(
        project_key=f"PROJECT{round(time.time())}",
        project_name=f"My Project {round(time.time())}",
        repository_name=f"avatar{round(time.time())}",
        pull_request_id="0",
        repo_to_clone="https://github.com/nanux/git-test-repo.git",
        folder="git-test-repo",
        new_branch="new-branch",
        user=f"user{round(time.time())}"
    )


@pytest.fixture(scope='session', autouse=True)
def data_cleanup(tdata, ctx, pytestconfig):
    yield

    if pytestconfig.getoption("--cleanup"):
        logging.info("Cleaning up the test data")
        # local repository
        shutil.rmtree(tdata.folder, ignore_errors=True)
        # user
        assert requests.delete(f"{ctx.base_url}/rest/api/1.0/admin/users?name={tdata.user}",
                               auth=ctx.admin_auth).status_code == 200
        # repository
        r = requests.delete(
            f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}",
            auth=ctx.admin_auth)
        assert r.status_code == 202 or r.status_code == 204, "cannot delete the repository"
        # project
        assert requests.delete(f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}",
                               auth=ctx.admin_auth).status_code == 204, "cannot delete the project"
