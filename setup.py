#!/usr/bin/env python3

from setuptools import setup

cmd_classes = {}
try:
    from setupext import janitor
    cmd_classes['clean'] = janitor.CleanCommand
except ImportError:
    import traceback
    traceback.print_exc()

setup(name='KompGen',
      version='0.2',
      description='Utilities for programming contests',
      author='Kevin Atienza',
      author_email='kevin.charles.atienza@gmail.com',
      entry_points={
          'console_scripts': [
              'kg = kg:main',
              'kg-kg = kg:main',
              'kg-kompgen = kg:main',
              'kg-pg = kg:main_pg',
              'kg-polygon = kg:main_pg',
              'kg-hr = kg:main_hr',
              'kg-hackerrank = kg:main_hr',
              'kg-aux = kg.script.aux:main',
          ],
      },
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
              'data/*.*',
              'data/template/*',
              'data/contest_template/*',
              'data/contest_template/pc2/*',
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
      setup_requires=[
          'setupext-janitor',
      ],
      cmdclass=cmd_classes,
)
