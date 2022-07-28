from pathlib import Path
import os
import jinja2 as j2

TEMPLATE_FILE = 'bitbucket-pipelines.yml.j2'
images = {
    'Bitbucket': {
        11: {
            'mac_key': 'bitbucket',
            'artefact': 'atlassian-bitbucket-software',
            'start_version': '7.5',
            'default_release': True,
            'base_image': 'eclipse-temurin:11',
            'tag_suffixes': ['jdk11','ubuntu-jdk11'],
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
    generated_output = template.render(images=images, batches=12)

    print(generated_output)

if __name__ == '__main__':
    main()
