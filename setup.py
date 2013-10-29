#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='pyramid_bimt',
    version='0.1',
    description='TOOD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pyramid',
        'SQLAlchemy',
        'passlib',
    ]
)
