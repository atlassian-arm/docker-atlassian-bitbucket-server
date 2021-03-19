import logging
import time
from pathlib import Path
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
        ["git", "clone", "--bare", tdata.repo_to_clone, tdata.bare_repo_folder])
    if clone_o.returncode not in (0, 128):
        pytest.fail(f"error when cloning repository, {clone_o}")

    logging.info("Git clone returned with exit code: %d", clone_o.returncode)

    url_parsed = urlparse(ctx.base_url)
    # example scm url:
    # http://admin:admin@localhost:7990/scm/project1615521268/avatar1615521268.git
    tdata.repo_host_url = f"{url_parsed.scheme}://{ctx.admin_user}:{ctx.admin_pwd}@{url_parsed.hostname}:{url_parsed.port}" \
                          f"/scm/{tdata.project_key.lower()}/{tdata.repository_name}.git"

    subprocess.run(
        ["git", "remote", "add", tdata.project_key, tdata.repo_host_url], cwd=tdata.bare_repo_folder)

    push_o = subprocess.run(
        ["git", "push", "--all", tdata.project_key], cwd=tdata.bare_repo_folder)

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
            "id": "refs/heads/main",
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
    tdata.pull_request_id = json_resp['id']
    assert json_resp['title'] == pr_title
    assert json_resp['open']


def test_commit_new_change_to_open_pull_request(ctx, tdata):
    subprocess.run(["git", "clone", tdata.bare_repo_folder, tdata.work_repo_folder])
    with open(Path(tdata.work_repo_folder, "new-file.txt"), "w") as f:
        f.write(f"new line with {tdata.search_needle} for search test")

    subprocess.run(["git", "checkout", "new-branch"], cwd=tdata.work_repo_folder)
    subprocess.run(["git", "add", "."], cwd=tdata.work_repo_folder)
    subprocess.run(["git", "commit", "-m", "new commit to the branch"], cwd=tdata.work_repo_folder)
    subprocess.run(["git", "remote", "add", tdata.project_key, tdata.repo_host_url], cwd=tdata.work_repo_folder)
    push_o = subprocess.run(["git", "push", tdata.project_key], cwd=tdata.work_repo_folder)

    print(push_o.stdout)
    assert push_o.returncode == 0, "there was a problem when pushing to remote"

    # TODO verify the pull request


def test_add_attachment(ctx, tdata):
    url = f"{ctx.base_url}/projects/{tdata.project_key}/repos/{tdata.repository_name}/attachments"
    files = {'files': ('file.txt', open('file.txt', 'rb'), 'multipart/form-data')}

    r = requests.post(url, files=files, auth=ctx.admin_auth)

    assert r.status_code == 201, f'failed to upload attachment, status: {r.status_code}, content: {r.text}'
    attachment_id = r.json()['attachments'][0]['id']

    download_url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/attachments/{attachment_id}"
    d = requests.get(download_url, auth=ctx.admin_auth)
    assert d.status_code == 200, f'failed to download attachment, status: {r.status_code}, content: {r.text}'
    assert 'filename="file.txt"' in d.headers['Content-Disposition'], r.headers


def test_add_general_comment_to_pr(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/pull-requests/{tdata.pull_request_id}/comments"

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


def test_approve_pull_request(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/pull-requests/{tdata.pull_request_id}/approve"

    # approve a pull request
    r = requests.post(url, headers=NOCHECK, auth=tdata.user_auth)

    assert r.status_code == 200, f'failed to approve the pull request, status: {r.status_code}, content: {r.text}'

    json_resp = r.json()
    assert json_resp['approved']


def test_merge_pull_request(ctx, tdata):
    url = f"{ctx.base_url}/rest/api/1.0/projects/{tdata.project_key}/repos/{tdata.repository_name}/pull-requests/{tdata.pull_request_id}/merge?version=1"

    # merge the pull request
    r = requests.post(url, headers=NOCHECK, auth=ctx.admin_auth)

    assert r.status_code == 200, f'failed to merge the pull request, status: {r.status_code}, content: {r.text}'

    json_resp = r.json()
    assert json_resp['id'] > 0
    assert json_resp['state'] == "MERGED"
    assert json_resp['closed']


def test_search(ctx, tdata):
    needle = tdata.search_needle
    url = f"{ctx.base_url}/rest/search/latest/search"
    payload = {"query": needle, "entities": {"code": {}},
               "limits": {"primary": 25, "secondary": 10}}

    found = False
    for i in range(0, 60):
        r = requests.post(url, auth=ctx.admin_auth, json=payload)
        if r.json()['code']['count'] == 1:
            print(f"waited {i} seconds for the search result")
            found = True
            break
        time.sleep(1)

    assert found, "Couldn't find the searched item"
