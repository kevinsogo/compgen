#!/usr/bin/env python3

from setuptools import setup

cmd_classes = {}
try:
    from setupext_janitor import janitor
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
              'kg-aux = kg.script.auxillary:main',
          ],
      },
      packages=[
          'kg',
          'kg.script',
          'kg.diff',
          'kg.black_magic',
          'kg.graphs',
          'kg.grids',
          'kg.utils',
          'kg.math',
      ],
      package_data={
          'kg': [
              'data/*.*',
              'data/template/*',
              'data/template/kg/*',
              'data/template/cms-it/*',
              'data/template/dom/*',
              'data/contest_template/*',
              'data/contest_template/pc2/*',
              'data/contest_template/cms-it/*',
              'data/contest_template/dom/*',
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
          'argcomplete',
          'pytz',
          'PyYAML'
      ],
      setup_requires=[
          'setupext-janitor',
      ],
      cmdclass=cmd_classes,
)
