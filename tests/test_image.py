import pytest

from helpers import get_app_home, get_app_install_dir, get_bootstrap_proc, get_procs, \
    parse_properties, parse_xml, run_image, wait_for_http_response, wait_for_proc

JAVA_BINARY = '/opt/java/openjdk/bin/java'


def test_first_run_state(docker_cli, image, run_user):
    PORT = 7990
    URL = f'http://localhost:{PORT}/status'

    container = run_image(docker_cli, image, user=run_user, ports={PORT: PORT})

    wait_for_http_response(URL, expected_status=503, expected_state=('STARTING', 'FIRST_RUN'))


def test_jvm_args(docker_cli, image, run_user):
    environment = {
        'JVM_MINIMUM_MEMORY': '383m',
        'JVM_MAXIMUM_MEMORY': '2047m',
        'JVM_SUPPORT_RECOMMENDED_ARGS': '-verbose:gc',
    }
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    jvm = [proc for proc in procs_list if proc.startswith(JAVA_BINARY) and 'BitbucketServerLauncher' in proc][0]

    assert f'-Xms{environment.get("JVM_MINIMUM_MEMORY")}' in jvm
    assert f'-Xmx{environment.get("JVM_MAXIMUM_MEMORY")}' in jvm
    assert environment.get('JVM_SUPPORT_RECOMMENDED_ARGS') in jvm


def test_elasticsearch_default(docker_cli, image, run_user):
    container = run_image(docker_cli, image, user=run_user)
    _es_jvm = wait_for_proc(container, 'org.elasticsearch.bootstrap.Elasticsearch')

    procs_list = get_procs(container)
    java_procs = [proc for proc in procs_list if proc.startswith(JAVA_BINARY)]
    assert len(java_procs) == 2


def test_elasticsearch_disabled(docker_cli, image, run_user):
    environment = {'ELASTICSEARCH_ENABLED': 'false'}
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    java_procs = [proc for proc in procs_list if proc.startswith(JAVA_BINARY)]
    assert len(java_procs) == 1
    assert 'org.elasticsearch.bootstrap.Elasticsearch' not in java_procs[0]


def test_application_mode_mirror(docker_cli, image, run_user):
    environment = {'APPLICATION_MODE': 'mirror'}
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    java_procs = [proc for proc in procs_list if proc.startswith(JAVA_BINARY)]
    assert len(java_procs) == 1
    assert 'org.elasticsearch.bootstrap.Elasticsearch' not in java_procs[0]


def test_install_permissions(docker_cli, image):
    container = run_image(docker_cli, image)

    assert container.file(f'{get_app_install_dir(container)}').user == 'root'
    assert container.file(f'{get_app_install_dir(container)}/app/META-INF/MANIFEST.MF').user == 'root'
    assert container.file(f'{get_app_install_dir(container)}/bin/start-bitbucket.sh').user == 'root'


def test_home_permissions(docker_cli, image):
    container = run_image(docker_cli, image)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    assert container.file(f'{get_app_home(container)}').user == 'bitbucket'


def test_java_in_run_user_path(docker_cli, image):
    RUN_USER = 'bitbucket'
    container = run_image(docker_cli, image)
    proc = container.run(f'su -c "which java" {RUN_USER}')
    assert len(proc.stdout) > 0


def test_git(docker_cli, image, run_user):
    container = run_image(docker_cli, image, user=run_user)
    container.run_test('git --version')
