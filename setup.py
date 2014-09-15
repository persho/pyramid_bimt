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
    version='0.17',
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
        'ColanderAlchemy',
        'Paste',
        'SQLAlchemy',
        'alembic',
        'celery[redis]',
        'cornice',
        'fanstatic [cssmin,jsmin]',
        'flufl.enum',
        'js.bootstrap',
        'js.deform',
        'js.jquery',
        'js.jquery-timeago',
        'js.jquery_datatables',
        'js.jquery_maskedinput',
        'passlib',
        'psycopg2',
        'pycrypto',
        'pyramid',
        'pyramid_basemodel',
        'pyramid_chameleon',
        'pyramid_beaker',
        'pyramid_celery',
        'pyramid_deform',
        'pyramid_fanstatic',
        'pyramid_layout',
        'pyramid_mailer',
        'pyramid_raven',
        'python-dateutil',
        'requests',
        'transaction',
        'ua-parser',
        'waitress',
    ],
    extras_require={
        'test': [
            'Sphinx',
            'coverage',
            'flake8',
            'mock',
            'nose',
            'nose-selecttests',
            'pyramid_robot',
            'robotframework-debuglibrary',
            'robotframework-httplibrary',
            'simplejson',
            'unittest2',
            'webtest',
            'zope.testing',
        ],
        'develop': [
            'Sphinx',
            'pyramid_debugtoolbar',
            'sadisplay',
            'zest.releaser',
        ],
    },
    entry_points="""\
    [paste.app_factory]
    main = pyramid_bimt:main

    # Fanstatic resource library
    [fanstatic.libraries]
    pyramid_bimt = pyramid_bimt.static:lib_bimt
    """,
)
