import logging
from urllib.parse import urlparse

import requests
import subprocess
import pytest


def test_create_project(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects"

    data = {
        "key": tdata.project_key,
        "name": tdata.project_name,
        "description": "The description for my cool project.",
    }

    r = requests.post(url, json=data, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to create project, status:{r.status_code}, content: {r.text}'
    assert r.json()['key'] == tdata.project_key


def test_create_repository(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos"

    data = {
        "name": tdata.repository_name,
        "scmId": "git",
        "forkable": True,
        "defaultBranch": "main"
    }

    r = requests.post(url, json=data, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to create repository, status: {r.status_code}, content: {r.text}'
    assert r.json()['name'] == tdata.repository_name
    assert r.json()['slug'] == tdata.repository_name.lower()


def test_import_repository(ctx, tdata):
    clone_o = subprocess.run(
        ["git", "clone", "--bare", tdata.repo_to_clone, tdata.folder])
    if clone_o.returncode not in (0, 128):
        pytest.fail(f"error when cloning repository, {clone_o}")

    url_parsed = urlparse(ctx.base_url)
    # example scm url:
    # http://admin:admin@localhost:7990/scm/project1615521268/avatar1615521268.git
    repo_host_url = f"{url_parsed.scheme}://{ctx.admin_user}:{ctx.admin_pwd}@{url_parsed.hostname}:{url_parsed.port}" \
                    f"/scm/{tdata.project_key.lower()}/{tdata.repository_name}.git"

    clone_o = subprocess.run(
        ["git", "remote", "add", tdata.project_key, repo_host_url], cwd=tdata.folder)

    logging.info("Git clone returned with exit code: %d", clone_o.returncode)

    push_o = subprocess.run(
        ["git", "push", "--mirror", tdata.project_key], cwd=tdata.folder)

    assert push_o.returncode == 0, "cannot push repository from local to bitbucket"
