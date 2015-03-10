#!/usr/bin/env python

from Queue import Queue
from threading import Thread
from termcolor import colored
from subprocess import Popen, PIPE

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


import os, sys, re
import shutil
import tarfile
import random, time

import flockr.config as config

class Control:

  __BUILD_DIRECTORY_NAME = 'flockr-build'

  cfg = None

  def __init__(self): pass

  def download_base_system(self):
    print colored('Base S.O. archive format:', 'yellow'), colored(self.cfg.get('build')['base_format'], 'green')
    print
    if self.cfg.get('build')['base_format'] == 'TAR':
      tar = tarfile.open(self.cfg.get('build')['base_url'])
      root_fs = '%s/root-fs' % (self.tmp_build_dir)
      try:
        print colored('=> Cleaning up tmpdir %s' % (root_fs), 'yellow')
        shutil.rmtree(root_fs)
        os.makedirs(root_fs)
      except Exception, e:
        print str(e)

      print colored('=> Extracting Base S.O. files to %s' % (root_fs), 'yellow')
      tar.extractall(root_fs)

  def clone_application(self):
    app_dir = '%s/app' % self.tmp_build_dir
    print colored('=> Fetching application from %s' % (self.cfg.get('build')['application_repository']), 'yellow')
    p = Popen(['/usr/bin/git','clone', self.cfg.get('build')['application_repository'], app_dir], stderr=PIPE, stdout=PIPE)
    res = p.communicate()
    if len(res[0]) == 0:
      print colored('=> ERROR:', 'yellow'), colored('%s' % ( res[1] ), 'red')

  def create(self, node): pass

  def delete(self, node): pass

  def build(self, name):
    # opening config
    self.cfg = config.Config('%s/config.yaml' % (name) )

    self.tmp_build_dir = '%s/%s'  % (self.cfg.get('build')['tmpdir'], \
        self.__BUILD_DIRECTORY_NAME)

    print colored( '\n* Building app %s *\n' % name, 'yellow')
    self.download_base_system()
    self.clone_application()

  def register(self): pass

  def app(self, name):
    try:
      os.mkdir(name)
      f = open('%s/config.yaml' % (name), 'w')
      f.write(open('lib/flockr/example/config.yaml','r').read())
      f.close()
    except Exception, e: pass

  def run(self, options):
    opts = ['create','delete','build','app']
    for opt in opts:
      if eval('options.%s' % opt):
        eval('self.%s("%s")' % (opt, options.name) )
