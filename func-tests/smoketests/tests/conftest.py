import logging
import os
import shutil
import subprocess
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
    search_needle: str
    pull_request_id: str
    bitbucket_version: str
    attachment_id: str
    attachment_link: str
    repo_to_clone: str
    bare_repo_folder: str
    work_repo_folder: str
    new_branch: str
    user: str

    def __post_init__(self):
        self.user_auth = HTTPBasicAuth(self.user, self.user)


@pytest.fixture(scope='session')
def ctx() -> Context:
    return Context(
        base_url=os.environ.get('BITBUCKET_BASE_URL', "http://bitbucket:8080"),
        admin_user=os.environ.get('BITBUCKET_ADMIN', 'admin'),
        admin_pwd=os.environ.get('BITBUCKET_ADMIN_PWD', 'admin'),
    )


@pytest.fixture(scope='session')
def tdata() -> TestData:
    return TestData(
        project_key=f"PROJECT{round(time.time())}",
        project_name=f"My Project {round(time.time())}",
        repository_name=f"avatar{round(time.time())}",
        bitbucket_version='6.0.1',
        pull_request_id="-1",
        attachment_id="-1",
        attachment_link="",
        search_needle=f"needle{time.time()}",
        repo_to_clone="https://github.com/nanux/git-test-repo.git",
        bare_repo_folder="git-test-repo",
        work_repo_folder="git-test-repo-work",
        new_branch="new-branch",
        user=f"user{round(time.time())}"
    )


@pytest.fixture(scope='session', autouse=True)
def git_config():
    subprocess.run(["git", "config", "--global", "user.email", "user@example.com"])
    subprocess.run(["git", "config", "--global", "user.name", "User Userson"])

    yield


@pytest.fixture(scope='session', autouse=True)
def data_cleanup(tdata, ctx, pytestconfig):
    yield

    if pytestconfig.getoption("--cleanup"):
        logging.info("Cleaning up the test data")
        # local repository
        shutil.rmtree(tdata.bare_repo_folder, ignore_errors=True)
        # local clone of the bare repository
        shutil.rmtree(tdata.work_repo_folder, ignore_errors=True)
        # user
        assert requests.delete(f"{ctx.base_url}/rest/api/1.0/admin/users?name={tdata.user}",
                               auth=ctx.admin_auth).status_code == 200
        # repository
        assert requests.delete(
            f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}",
            auth=ctx.admin_auth).status_code == 202, "cannot delete the repository"

        # project
        assert requests.delete(f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}",
                               auth=ctx.admin_auth).status_code == 204, "cannot delete the project"
