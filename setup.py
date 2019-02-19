#!/usr/bin/env python

from setuptools import setup

setup(name='KompGen',
      version='0.2',
      description='Utilities for programming contests',
      author='Kevin Atienza',
      author_email='kevin.charles.atienza@gmail.com',
      packages=[
          'kg',
          'kg.script',
          'kg.diff',
          'kg.black_magic',
          'kg.graphs',
          'kg.utils',
          'kg.math',
      ],
      package_data={
          'kg': [
              'data/*',
              'data/template/*',
              'data/contest_template/*',
              'data/contest_template/pc2/*'
          ],
          'kg.diff': [
              'templates/*',
          ],
      },
      install_requires=[
          'natsort',
          'colorama',
          'termcolor',
          'Jinja2',
      ],
)
