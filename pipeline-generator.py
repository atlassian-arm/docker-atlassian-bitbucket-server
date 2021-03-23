from pathlib import Path
import os
import jinja2 as j2

TEMPLATE_FILE = 'bitbucket-pipelines.yml.j2'
images = {
    'Bitbucket': {
        11: {
            'mac_key': 'bitbucket',
            'artefact': 'atlassian-bitbucket-software',
            'start_version': '6',
            'end_version': '8',
            'default_release': False,
            'base_image': 'adoptopenjdk:11-hotspot',
            'tag_suffixes': ['jdk11','ubuntu-jdk11'],
            'docker_repos': ['atlassian/bitbucket', 'atlassian/bitbucket-server'],
        },
        8: {
            'mac_key': 'bitbucket',
            'artefact': 'atlassian-bitbucket-software',
            'start_version': '6',
            'end_version': '8',
            'default_release': True,
            'base_image': 'adoptopenjdk:8-hotspot',
            'tag_suffixes': ['jdk8','ubuntu','ubuntu-jdk8'],
            'docker_repos': ['atlassian/bitbucket', 'atlassian/bitbucket-server'],
        }
    }
}


def main():
    jenv = j2.Environment(
        loader=j2.FileSystemLoader('.'),
        lstrip_blocks=True,
        trim_blocks=True)
    template = jenv.get_template(TEMPLATE_FILE)
    generated_output = template.render(images=images, batches=15)

    print(generated_output)

if __name__ == '__main__':
    main()
