#!/usr/bin/env python

from setuptools import setup

setup(name='KompGen',
      version='0.2',
      description='Utilities for programming contests',
      author='Kevin Atienza',
      author_email='kevin.charles.atienza@gmail.com',
      packages=['kg', 'kg.diff', 'kg.black_magic'],
      package_data={'kg': ['data/*.json', 'data/template/*'], 'kg.diff': ['templates/*']},
      # TODO add 'natsort' as a dependency
     )
