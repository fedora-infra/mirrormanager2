#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources
import re

from setuptools import setup


with open('mirrormanager2/__init__.py') as stream:
    __version__ = re.compile(
        r".*__version__ = '(.*?)'", re.S
    ).match(stream.read()).group(1)


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()

    return [
        line.strip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='mirrormanager2',
    description='MirrorManager2 is the application used to managed the Fedora '
        'mirrors all over the world.',
    version=__version__,
    author='Fedora Infrastructure team',
    author_email='admin@fedoraproject.org',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='MIT',
    download_url='https://github.com/fedora-infra/mirrormanager2/releases',
    url='https://github.com/fedora-infra/mirrormanager2/',
    packages=['mirrormanager2'],
    include_package_data=True,
    install_requires=get_requirements() + get_requirements(
        'requirements_mirrorlist.txt'),
    scripts = [
        'client/report_mirror',
        'mirrorlist/mirrorlist_statistics',
        'utility/mm2_crawler',
        'utility/mm2_emergency-expire-repo',
        'utility/mm2_generate-worldmap',
        'utility/mm2_get_global_netblocks',
        'utility/mm2_get_internet2_netblocks',
        'utility/mm2_move-devel-to-release',
        'utility/mm2_move-to-archive',
        'utility/mm2_propagation',
        'utility/mm2_refresh_mirrorlist_cache',
        'utility/mm2_update-EC2-netblocks',
        'utility/mm2_update-master-directory-list',
        'utility/mm2_umdl2',
        'utility/mm2_update-mirrorlist-server',
        'utility/mm2_create_install_repo',
        'utility/mm2_upgrade-install-repo',
    ],
)
