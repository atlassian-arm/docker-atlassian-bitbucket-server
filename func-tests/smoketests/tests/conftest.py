import os
import time
from dataclasses import dataclass

import pytest
from requests.auth import HTTPBasicAuth


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
        repository_name=f"avatar{round(time.time())}"
    )
