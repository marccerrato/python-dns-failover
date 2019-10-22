#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='python-dns-failover',
    version='0.1.0',
    description='Python script to automatically update DNS records for a bunch of servers participating in a Round-Robin DNS setup.',
    long_description=readme + '\n\n' + history,
    author='Marc Cerrato',
    author_email='marccerrato@gmail.com',
    url='https://github.com/marccerrato/python-dns-failover',
    packages=[
        'dns_failover',
    ],
    package_dir={'dns_failover': 'dns_failover'},
    include_package_data=True,
    install_requires=[
        "requests==2.20.0",
    ],
    license="BSD",
    zip_safe=False,
    keywords='python-dns-failover',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='tests',
)