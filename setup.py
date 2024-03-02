#!/usr/bin/env python3
from setuptools import setup, find_packages

import json
import os

def read_pipenv_dependencies(fname):
    filepath = os.path.join(os.path.dirname(__file__), fname)
    with open(filepath) as lockfile:
        lockjson = json.load(lockfile)
        return [dependency for dependency in lockjson.get('default')]

if __name__ == '__main__':
    setup(
        name='sync4shikimori2mal',
        version=os.getenv('PACKAGE_VERSION', '0.0.dev0'),
        package_dir={'': 'src'},
        packages=find_packages('src', include=[
            'sync4s2m*'
        ]),
        description='Script for lists synchronization between Shikimori (source) and MyAnimeList (target).',
        install_requires=[
              *read_pipenv_dependencies('Pipfile.lock'),
        ]
    )
