#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='dxfile',
    author='David Vine, Francesco De Carlo',
    packages=find_packages(),
    version=open('VERSION').read().strip(),
    description = 'Reader/Writer for Data Exchange files.',
    license='BSD-3',
    platforms='Any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: BSD-3',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
    ]
)
