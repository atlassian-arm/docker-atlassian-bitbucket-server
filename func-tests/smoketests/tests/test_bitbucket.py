import requests


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
