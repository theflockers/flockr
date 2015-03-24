#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='Flockr',
      version='0.1',
      description='Cloudstack container management',
      url='https://github.com/theflockers/flockr',
      author='Leandro Mendes',
      author_email='theflockers@gmail.com',
#      packages = ['flockr.cmdline','flockr.config','flockr.control'],
      package_dir = {'': 'lib'},
      packages = find_packages('lib'),
      install_requires =['CloudStack','filemagic'],
      scripts = ['bin/flockr'],
      data_files = [('flockr', ['config.yaml-example','flockr.yaml'])],
    )
