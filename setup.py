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
    version='0.1.9.dev0',
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
    install_requires=[
        'pyramid',
        'pyramid_basemodel',
        'pyramid_deform',
        'pyramid_layout',
        'pyramid_mailer',
        'SQLAlchemy',
        'ColanderAlchemy>=0.3.dev0',
        'passlib',
        'pyramid_raven',
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
        'development': [
            'pyramid_debugtoolbar',
            'Sphinx',
            'waitress',
            'zest.releaser',
        ],
    },
    entry_points="""\
    [paste.app_factory]
    main = pyramid_bimt:main
    """,
)
