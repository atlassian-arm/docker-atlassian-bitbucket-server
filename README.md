![Atlassian Bitbucket Server](https://wac-cdn.atlassian.com/dam/jcr:bf39fc40-3871-491f-98e3-fb2293f57a00/bitbucket-icon-gradient-blue.svg?cdnVersion=696)

Bitbucket Server is an on-premises source code management solution for Git
that's secure, fast, and enterprise grade. Create and manage repositories, set
up fine-grained permissions, and collaborate on code - all with the flexibility
of your servers.

Learn more about Bitbucket Server: <https://www.atlassian.com/software/bitbucket/server>

# Contents

[TOC]

# Overview

This Docker container makes it easy to get an instance of Bitbucket up and
running.

This Docker image is published as both `atlassian/bitbucket` and
`atlassian/bitbucket-server`. These are the same image, but the `-server`
version is deprecated and only kept for backwards-compatibility; for new
installations it is recommended to use the shorter name.

** NOTE: For backwards-compatibility, by default the image will start both
Bitbucket and an embedded OpenSearch. However this is not a recommended
configuration, especially in a clustered environment, and has known issues with
shutdown. instead, we recommend running a separate OpenSearch instance
(possibly in another Docker container); see below for instructions on connecting
to an external OpenSearch cluster. **

** If running this image in a production environment, we strongly recommend you
run this image using a specific version tag instead of latest. This is because
the image referenced by the latest tag changes often and we cannot guarantee
that it will be backwards compatible. **

** Use docker version >= 20.10.10 **

# Quick Start

For the `BITBUCKET_HOME` directory that is used to store the repository data
(amongst other things) we recommend mounting a host directory as a
[data volume](https://docs.docker.com/engine/tutorials/dockervolumes/#/data-volumes),
or via a named volume.

Additionally, if running Bitbucket in Data Center mode it is required that a
shared filesystem is mounted.

Volume permission is managed by entry scripts. To get started you can use a data
volume, or named volumes. In this example we'll use named volumes.

    $> docker volume create --name bitbucketVolume
    $> docker run -v bitbucketVolume:/var/atlassian/application-data/bitbucket --name="bitbucket" -d -p 7990:7990 -p 7999:7999 atlassian/bitbucket

Note that this command can substitute folder paths with named volumes.

Start Atlassian Bitbucket Server:

    $> docker run -v /data/bitbucket:/var/atlassian/application-data/bitbucket --name="bitbucket" -d -p 7990:7990 -p 7999:7999 atlassian/bitbucket

**Success**. Bitbucket is now available on [http://localhost:7990](http://localhost:7990)*

Please ensure your container has the necessary resources allocated to it.
We recommend 2GiB of memory allocated to accommodate both the application server
and the git processes.
See [Supported Platforms](https://confluence.atlassian.com/display/BitbucketServer/Supported+platforms) for further information.


_* Note: If you are using `docker-machine` on Mac OS X, please use `open http://$(docker-machine ip default):7990` instead._

## Common settings

### Reverse Proxy Settings

If Bitbucket is run behind a reverse proxy server as
[described here](https://confluence.atlassian.com/bitbucketserver/proxying-and-securing-bitbucket-server-776640099.html),
then you need to specify extra options to make Bitbucket aware of the
setup. They can be controlled via the below environment variables.

* `SERVER_PROXY_NAME` (default: NONE)

   The reverse proxy's fully qualified hostname.

* `SERVER_PROXY_PORT` (default: NONE)

   The reverse proxy's port number via which bitbucket is accessed.

* `SERVER_SCHEME` (default: http)

   The protocol via which bitbucket is accessed. 
   
   In certain cloud environments (specifically Kubernetes, Heroku and Cloud Foundry), this setting
   will be superseded by the value of the `X-Forwarded-Proto` request header if sent by a ingress or load balancer. 
   See `SERVER_FORWARD_HEADERS_STRATEGY` below to alter this behaviour.

* `SERVER_SECURE` (default: false)

   Set 'true' if SERVER\_SCHEME is 'https'. 

* `SERVER_FORWARD_HEADERS_STRATEGY` (default: NATIVE in the specified cloud environments, NONE otherwise)

   Can be explicitly set to a value of `NONE` if deploying to a cloud environment (specifically Kubernetes, Heroku and Cloud Foundry) and the preference is for `SERVER_SCHEME` 
   to be used over the value of the `X-Forwarded-Proto` request header. A value of NONE will cause X-Forwarded-* headers to no longer take priority when determining the 
   origin of a request, which means the system will return to the default expected state.

### JVM Configuration (Bitbucket Server 5.0 + only)

If you need to override Bitbucket Server's default memory configuration or pass
additional JVM arguments, use the environment variables below

* `JVM_MINIMUM_MEMORY` (default: 512m)

   The minimum heap size of the JVM

* `JVM_MAXIMUM_MEMORY` (default: 1024m)

   The maximum heap size of the JVM

* `JVM_SUPPORT_RECOMMENDED_ARGS` (default: NONE)

   Additional JVM arguments for Bitbucket Server, such as a custom Java Trust Store

### Application Mode Settings (Bitbucket Server 5.0 + only)

This docker image can be run as a
[Smart Mirror](https://confluence.atlassian.com/bitbucketserver/smart-mirroring-776640046.html)
or as part of a
[Data Center](https://confluence.atlassian.com/enterprise/bitbucket-data-center-668468332.html)
cluster.  You can specify the following properties to start Bitbucket as a
mirror or as a Data Center node:

* `SEARCH_ENABLED` (default: true)

  Set 'false' to prevent OpenSearch (previously Elasticsearch) from starting in the
  container. This should be used if OpenSearch is running remotely, e.g. for if Bitbucket
  is running in a Data Center cluster. You may also use `ELASTICSEARCH_ENABLED` to
  set this property, however this is deprecated in favor of `SEARCH_ENABLED`.

* `APPLICATION_MODE` (default: default)

   The mode Bitbucket will run in. This can be set to 'mirror' to start
   Bitbucket as a Smart Mirror. This will also disable OpenSearch even if
   `SEARCH_ENABLED` has not been set to 'false'.

### Database Configuration

To configure the database automatically on first run, you can provide the
following settings:

* `JDBC_DRIVER`
* `JDBC_URL`
* `JDBC_USER`
* `JDBC_PASSWORD`

Note: Due to licensing restrictions Bitbucket does not ship with a MySQL or
Oracle JDBC drivers. To use these databases you will need to copy a suitable
driver into the container and restart it. For example, to copy the MySQL driver
into a container named "bitbucket", you would do the following:

    docker cp mysql-connector-java.x.y.z.jar bitbucket:/var/atlassian/application-data/bitbucket/lib
    docker restart bitbucket

For more information see [Connecting Bitbucket Server to an external database](https://confluence.atlassian.com/bitbucketserver/connecting-bitbucket-server-to-an-external-database-776640378.html).

## Other settings

As well as the above settings, all settings that are available in the
[bitbucket.properties file](https://confluence.atlassian.com/bitbucketserver/bitbucket-server-config-properties-776640155.html)
can also be provided via Docker environment variables. For a full explanation of converting Bitbucket properties into environment
variables see
[the relevant Spring Boot documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/boot-features-external-config.html#boot-features-external-config-relaxed-binding).

For example, a full command-line for a Bitbucket node with a PostgreSQL
database, and an external OpenSearch instance might look like:

    $> docker network create --driver bridge --subnet=172.18.0.0/16 myBitbucketNetwork
    $> docker run --network=myBitbucketNetwork --ip=172.18.1.1 \
        -e SEARCH_ENABLED=false \
        -e JDBC_DRIVER=org.postgresql.Driver \
        -e JDBC_USER=atlbitbucket \
        -e JDBC_PASSWORD=MYPASSWORDSECRET \
        -e JDBC_URL=jdbc:postgresql://my.database.host:5432/bitbucket \
        -e PLUGIN_SEARCH_CONFIG_BASEURL=http://my.opensearch.host \
        -v /data/bitbucket-shared:/var/atlassian/application-data/bitbucket/shared \
        --name="bitbucket" \
        -d -p 7990:7990 -p 7999:7999 \
        atlassian/bitbucket

### Cluster settings

If running a clustered Bitbucket DC instance, the cluster settings are specified
with `HAZELCAST_*` environment variables. The main ones to be aware of are:

* `HAZELCAST_PORT` (`hazelcast.port`)
* `HAZELCAST_GROUP_NAME` (`hazelcast.group.name`)
* `HAZELCAST_GROUP_PASSWORD` (`hazelcast.group.password`)

Each clustering type (e.g. AWS/Azure/Multicast/TCP) has its own settings. For
more information on clustering Bitbucket, and other properties see
[Clustering with Bitbucket Data Center](https://confluence.atlassian.com/bitbucketserver/clustering-with-bitbucket-data-center-776640164.html)
and [Clustering with Bitbucket Data Center](https://confluence.atlassian.com/bitbucketserver/bitbucket-server-config-properties-776640155.html).

**NOTE:** The underlying network should be configured to support the clustering
type you are using. How to do this depends on the container management
technology, and is beyond the scope of this documentation.

### JMX Monitoring

JMX monitoring can be enabled with `JMX_ENABLED=true`. Information
on additional settings and available metrics is available in the
[Bitbucket JMX documentation](https://confluence.atlassian.com/bitbucketserver/enabling-jmx-counters-for-performance-monitoring-776640189.html).

## Container Configuration

* `SET_PERMISSIONS` (default: true)

   Define whether to set home directory permissions on startup. Set to `false` to disable
   this behaviour.

# Shared directory and user IDs

By default the Bitbucket application runs as the user `bitbucket`, with a UID
and GID of 2003. Consequently this UID must have write access to the shared
filesystem. If for some reason a different UID must be used, there are a number
of options available:

* The Docker image can be rebuilt with a different UID.
* Under Linux, the UID can be remapped using
  [user namespace remapping](https://docs.docker.com/engine/security/userns-remap/).

# Upgrade

To upgrade to a more recent version of Bitbucket Server you can simply stop the `bitbucket`
container and start a new one based on a more recent image:

    $> docker stop bitbucket
    $> docker rm bitbucket
    $> docker pull atlassian/bitbucket:<desired_version>
    $> docker run ... (See above)

As your data is stored in the data volume directory on the host it will still
be available after the upgrade.

_Note: Please make sure that you **don't** accidentally remove the `bitbucket`
container and its volumes using the `-v` option._

# Backup

For evaluations you can use the built-in database that will store its files in
the Bitbucket Server home directory. In that case it is sufficient to create a
backup archive of the directory on the host that is used as a volume
(`/data/bitbucket` in the example above).

The [Bitbucket Server Backup Client](https://confluence.atlassian.com/display/BitbucketServer/Data+recovery+and+backups)
is currently not supported in the Docker setup. You can however use the
[Bitbucket Server DIY Backup](https://confluence.atlassian.com/display/BitbucketServer/Using+Bitbucket+Server+DIY+Backup)
approach in case you decided to use an external database.

Read more about data recovery and backups:
[https://confluence.atlassian.com/display/BitbucketServer/Data+recovery+and+backups](https://confluence.atlassian.com/display/BitbucketServer/Data+recovery+and+backups)

# Shutdown

Bitbucket allows a configurable grace period for active operations to finish
before termination; by default this is 30s. If sending a `docker stop` this
should be taken into account with the `--time` flag.

Alternatively, the script `/shutdown-wait.sh` is provided, which will initiate a
clean shutdown and wait for the process to complete. This is the recommended
method for shutdown in environments which provide for orderly shutdown,
e.g. Kubernetes via the `preStop` hook.

# Versioning

The `latest` tag matches the most recent version of this repository. Thus using
`atlassian/bitbucket:latest` or `atlassian/bitbucket` will ensure you are
running the most up to date version of this image.

Alternatively, you can use a specific minor version of Bitbucket Server by
using a version number tag: `atlassian/bitbucket:6`. This will
install the latest `6.x.x` version that is available.

# Supported JDK versions

All the Atlassian Docker images are now JDK11 only, and generated from the
[official Eclipse Temurin OpenJDK Docker images](https://hub.docker.com/_/eclipse-temurin).

The Docker images follow the [Atlassian Support end-of-life
policy](https://confluence.atlassian.com/support/atlassian-support-end-of-life-policy-201851003.html);
images for unsupported versions of the products remain available but will no longer
receive updates or fixes.

Historically, we have also generated other versions of the images, including
JDK8, Alpine, and 'slim' versions of the JDK. These legacy images still exist in
Docker Hub, however they should be considered deprecated, and do not receive
updates or fixes.

If for some reason you need a different version, see "Building your own image"

# Building your own image

* Clone the Atlassian repository at https://bitbucket.org/atlassian-docker/docker-atlassian-bitbucket-server/
* Modify or replace the [Jinja](https://jinja.palletsprojects.com/) templates
  under `config`; _NOTE_: The files must have the `.j2` extensions. However you
  don't have to use template variables if you don't wish.
* Build the new image with e.g: `docker build --tag my-bitbucket-image --build-arg BITBUCKET_VERSION=8.x.x .`
* Optionally push to a registry, and deploy.

# Supported architectures

Currently the Atlassian Docker images are built for the `linux/amd64` target
platform; we do not have other architectures on our roadmap at this
point. However the Dockerfiles and support tooling have now had all
architecture-specific components removed, so if necessary it is possible to
build images for any platform supported by Docker.

## Building on the target architecture

The simplest method of getting a platform image is to build it on a target
machine; see "Building your own image" above.

Note: This method is known to work on Mac M1 and AWS ARM64 machines, but has not
be extensively tested.

# Troubleshooting

These images include built-in scripts to assist in performing common JVM diagnostic tasks.

## Thread dumps

`/opt/atlassian/support/thread-dumps.sh` can be run via `docker exec` to easily trigger the collection of thread
dumps from the containerized application. For example:

    docker exec my_container /opt/atlassian/support/thread-dumps.sh

By default this script will collect 10 thread dumps at 5 second intervals. This can
be overridden by passing a custom value for the count and interval, by using `-c` / `--count`
and `-i` / `--interval` respectively. For example, to collect 20 thread dumps at 3 second intervals:

    docker exec my_container /opt/atlassian/support/thread-dumps.sh --count 20 --interval 3

Thread dumps will be written to `$APP_HOME/thread_dumps/<date>`.

Note: By default this script will also capture output from top run in 'Thread-mode'. This can
be disabled by passing `-n` / `--no-top`

## Heap dump

`/opt/atlassian/support/heap-dump.sh` can be run via `docker exec` to easily trigger the collection of a heap
dump from the containerized application. For example:

    docker exec my_container /opt/atlassian/support/heap-dump.sh

A heap dump will be written to `$APP_HOME/heap.bin`. If a file already exists at this
location, use `-f` / `--force` to overwrite the existing heap dump file.

## Manual diagnostics

The `jcmd` utility is also included in these images and can be used by starting a `bash` shell
in the running container:

    docker exec -it my_container /bin/bash


# Support

For product support, go to [support.atlassian.com](https://support.atlassian.com/)

You can also visit the [Atlassian Data Center on
Kubernetes](https://community.atlassian.com/t5/Atlassian-Data-Center-on/gh-p/DC_Kubernetes)
forum for discussion on running Atlassian Data Center products in containers.

# Changelog

For a detailed list of changes to the Docker image configuration see [the Git
commit history](https://bitbucket.org/atlassian-docker/docker-atlassian-bitbucket-server/commits/).

# License

Copyright © 2019 Atlassian Corporation Pty Ltd.
Licensed under the Apache License, Version 2.0.
