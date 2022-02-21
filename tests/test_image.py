import logging
import pytest
import requests
import signal
import testinfra

from helpers import get_app_home, get_app_install_dir, get_bootstrap_proc, get_procs, \
    parse_properties, parse_xml, run_image, \
    wait_for_http_response, wait_for_proc, wait_for_state, wait_for_log


PORT = 7990
URL = f'http://localhost:{PORT}/status'


def test_first_run_state(docker_cli, image, run_user):
    container = run_image(docker_cli, image, user=run_user, ports={PORT: PORT})

    wait_for_http_response(URL, expected_status=503, expected_state=('STARTING', 'FIRST_RUN'))


def test_clean_shutdown(docker_cli, image, run_user):
    # 7.14 and 7.15 have a known issue with shutdown logging, see BSERV-12919
    version = image.labels.get("product_version")
    if version in ['7.14.0', '7.14.1', '7.15.0', '7.15.1']:
        logging.warning(f"Skipping test_clean_shutdown for version {version}")
        return

    environment = {'SEARCH_ENABLED': 'false'}
    container = docker_cli.containers.run(image, detach=True, user=run_user,
                                          ports={PORT: PORT}, environment=environment)
    host = testinfra.get_host("docker://"+container.id)
    wait_for_state(URL, expected_state='FIRST_RUN')

    container.kill(signal.SIGTERM)

    # Check for final shutdown log. This message has been consistent across versions:
    #     c.a.b.i.boot.log.BuildInfoLogger Bitbucket 7.12.0 has shut down
    #     c.a.b.i.boot.log.BuildInfoLogger Bitbucket 6.3.6 has shut down
    end = r'c\.a\.b\.i\.boot\.log\.BuildInfoLogger Bitbucket \d+\.\d+\.\d+(?:-\w+)* has shut down'
    wait_for_log(container, end)


def test_shutdown_script(docker_cli, image, run_user):
    # 7.14 and 7.15 have a known issue with shutdown logging, see BSERV-12919
    version = image.labels.get("product_version")
    if version in ['7.14.0', '7.14.1', '7.15.0', '7.15.1']:
        logging.warning(f"Skipping test_clean_shutdown for version {version}")
        return

    environment = {'SEARCH_ENABLED': 'false'}
    container = docker_cli.containers.run(image, detach=True, user=run_user,
                                          ports={PORT: PORT}, environment=environment)
    host = testinfra.get_host("docker://"+container.id)
    wait_for_state(URL, expected_state='FIRST_RUN')

    container.exec_run('/shutdown-wait.sh')

    # Check for final shutdown log. This message has been consistent across versions:
    #     c.a.b.i.boot.log.BuildInfoLogger Bitbucket 7.12.0 has shut down
    #     c.a.b.i.boot.log.BuildInfoLogger Bitbucket 6.3.6 has shut down
    end = r'c\.a\.b\.i\.boot\.log\.BuildInfoLogger Bitbucket \d+\.\d+\.\d+(?:-\w+)* has shut down'
    wait_for_log(container, end)


def test_jvm_args(docker_cli, image, run_user):
    environment = {
        'JVM_MINIMUM_MEMORY': '383m',
        'JVM_MAXIMUM_MEMORY': '2047m',
        'JVM_SUPPORT_RECOMMENDED_ARGS': '-verbose:gc',
    }
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    jvm = [proc for proc in procs_list if get_bootstrap_proc(container) in proc][0]

    assert f'-Xms{environment.get("JVM_MINIMUM_MEMORY")}' in jvm
    assert f'-Xmx{environment.get("JVM_MAXIMUM_MEMORY")}' in jvm
    assert environment.get('JVM_SUPPORT_RECOMMENDED_ARGS') in jvm


def test_search_default(docker_cli, image, run_user):
    container = run_image(docker_cli, image, user=run_user)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    start_bitbucket = [proc for proc in procs_list if 'start-bitbucket.sh' in proc][0]
    assert '--no-search' not in start_bitbucket

    version = image.labels.get("product_version")
    sortable_version = [int(n) for n in version.split(".")]
    if sortable_version < [7, 21, 0]:
        search_jvm_proc = 'org.elasticsearch.bootstrap.Elasticsearch'
    else:
        search_jvm_proc = 'org.opensearch.bootstrap.OpenSearch'

    _search_jvm = wait_for_proc(container, search_jvm_proc)


def test_search_disabled(docker_cli, image, run_user):
    environment = {'SEARCH_ENABLED': 'false'}
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    jvms = [proc for proc in procs_list if '/opt/java/openjdk/bin/java' in proc]
    assert len(jvms) == 1
    assert "BitbucketServerLauncher" in jvms[0]


def test_application_mode_mirror(docker_cli, image, run_user):
    environment = {'APPLICATION_MODE': 'mirror'}
    container = run_image(docker_cli, image, user=run_user, environment=environment)
    _jvm = wait_for_proc(container, get_bootstrap_proc(container))

    procs_list = get_procs(container)
    jvms = [proc for proc in procs_list if '/opt/java/openjdk/bin/java' in proc]
    assert len(jvms) == 1
    assert "BitbucketServerLauncher" in jvms[0]


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
