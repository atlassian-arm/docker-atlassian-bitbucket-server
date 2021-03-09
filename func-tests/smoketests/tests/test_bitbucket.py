import requests
import json
import os
import time

from requests.models import HTTPBasicAuth

BASE_REST_URL = os.environ.get('BITBUCKET_BASE_URL', "http://localhost:7990")
user = os.environ.get('BITBUCKET_ADMIN', 'admin')
password = os.environ.get('BITBUCKET_ADMIN_PWD', 'admin')
auth = HTTPBasicAuth(user, password)

project_key = f"PROJECT{round(time.time())}"
project_name= f"My Project {round(time.time())}"
repository_name = f"avatar{round(time.time())}"


def test_create_project():
    url = f"{BASE_REST_URL}/rest/api/1.0/projects"

    data = {
        "key": project_key,
        "name": project_name,
        "description": "The description for my cool project.",
    }
    headers = {'Content-Type': 'application/json'}

    r = requests.post(url, json=data, headers=headers, auth=auth)
    data = r.json()

    assert r.status_code == 201, f'failed to create project, status:{r.status_code}, content: {r.text}'
    assert data['key'] == project_key


def test_create_repository():
    url = f"{BASE_REST_URL}/rest/api/1.0/projects/{project_key}/repos"

    data = {
        "name": repository_name,
        "scmId": "git",
        "forkable": True,
        "defaultBranch": "main"
    }
    headers = {'Content-Type': 'application/json'}

    r = requests.post(url, json=data, headers=headers, auth=auth)
    data = r.json()

    assert r.status_code == 201, f'failed to create repository, status: s{r.status_code}, content: {r.text}'
    assert data['name'] == repository_name
    assert data['slug'] == repository_name.lower()
