# -*- coding: utf-8 -*-
"""Installer for the pyramid_bimt package."""

from setuptools import find_packages
from setuptools import setup

import os


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


long_description = \
    read('README.rst') + \
    read('docs', 'CHANGELOG.rst') + \
    read('docs', 'LICENSE.rst')

setup(
    name='pyramid_bimt',
    version='0.1',
    description='Base package for BIMT apps.',
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='NiteoWeb Ltd.',
    author_email='info@niteoweb.com',
    keywords='python pyramid sqlalchemy',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    paster_plugins=['pyramid'],
    install_requires=[
        'pyramid',
        'pyramid_basemodel',
        'pyramid_layout',
        'SQLAlchemy',
        'ColanderAlchemy>=0.3.dev0',
        'passlib',
    ],
    extras_require={
        'test': [
            'coverage',
            'flake8',
            'mock',
            'nose',
            'nose-selecttests',
            'unittest2',
            'webtest',
        ],
    },
    dependency_links=
        ["https://github.com/stefanofontanelli/ColanderAlchemy/archive/2abcc36a17bb4680a872938717f3af250f22b1db.tar.gz#ColanderAlchemy-0.3.dev0"],
)
