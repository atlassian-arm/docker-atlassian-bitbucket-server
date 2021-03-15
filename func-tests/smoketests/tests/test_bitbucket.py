import logging
from urllib.parse import urlparse

import requests
import subprocess
import pytest

NOCHECK = {"X-Atlassian-Token": "no-check"}


def test_create_user(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/admin/users?name={tdata.user}&password={tdata.user}&displayName=User&emailAddress=user@example.com"

    r = requests.post(url, auth=ctx.admin_auth, headers=NOCHECK)

    assert r.status_code == 204, f'failed to create user, status:{r.status_code}, content: {r.text}'


def test_make_user_admin(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/admin/permissions/users?name={tdata.user}&permission=ADMIN"

    r = requests.put(url, auth=ctx.admin_auth, headers=NOCHECK)

    assert r.status_code == 204, f'failed to make the user an admin, status:{r.status_code}, content: {r.text}'


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

    logging.info("Git clone returned with exit code: %d", clone_o.returncode)

    url_parsed = urlparse(ctx.base_url)
    # example scm url:
    # http://admin:admin@localhost:7990/scm/project1615521268/avatar1615521268.git
    repo_host_url = f"{url_parsed.scheme}://{ctx.admin_user}:{ctx.admin_pwd}@{url_parsed.hostname}:{url_parsed.port}" \
                    f"/scm/{tdata.project_key.lower()}/{tdata.repository_name}.git"

    subprocess.run(
        ["git", "remote", "add", tdata.project_key, repo_host_url], cwd=tdata.folder)

    push_o = subprocess.run(
        ["git", "push", "--mirror", tdata.project_key], cwd=tdata.folder)

    assert push_o.returncode == 0, "cannot push repository from local to bitbucket"


def test_open_pull_request(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/pull-requests"

    pr_title = "The best PR in the world"
    data = {
        "title": pr_title,
        "description": "It’s a kludge, but put the tuple from the database in the cache.",
        "state": "OPEN",
        "open": True,
        "fromRef": {
            "id": f"refs/heads/{tdata.new_branch}",
        },
        "toRef": {
            "id": "refs/heads/master",
        },
        "reviewers": [
            {
                "user": {
                    "name": tdata.user
                }
            }
        ]
    }

    r = requests.post(url, json=data, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to create pull request, status: {r.status_code}, content: {r.text}'
    json_resp = r.json()
    assert json_resp['id'] > 0
    assert json_resp['title'] == pr_title
    assert json_resp['open']


def test_add_attachment(ctx, tdata):
    # headers = {"Content-Type": "multipart/form-data"}
    url = f"{ctx.base_url}/projects/{tdata.project_key}/repos/{tdata.repository_name}/attachments"
    files = {'files': open('file.txt', 'rb')}

    r = requests.post(url, files=files, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to upload attachment, status: {r.status_code}, content: {r.text}'

    attachment_url = r.json()['attachments'][0]['url']

    # TODO display attachment and pass it tdata so it can be attached to a comment
    # assert requests.get(attachment_url, auth=ctx.admin_auth).text == 'bla'


def test_add_general_comment_to_pr(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/pull-requests/1/comments"

    # inserts general comment on PR
    comment_text = "An insightful general comment on a pull request."
    data = {
        "text": comment_text
    }
    r = requests.post(url, json=data, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to create comment on the pull request, status: {r.status_code}, content: {r.text}'

    json_resp = r.json()
    assert json_resp['id'] > 0
    assert json_resp['text'] == comment_text
