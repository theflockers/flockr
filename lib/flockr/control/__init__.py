#!/usr/bin/env python

from Queue import Queue
from threading import Thread
from pprint import pprint

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import ConfigParser
import os, sys, re
import tarfile
import random, time

import flockr.config as config

class Control:

  __BUILD_DIRECTORY_NAME = 'flockr-build'

  cfg = None

  def __init__(self): pass    

  def download_base(self):
    print self.cfg.get('build')
    if self.cfg.get('build')['base_format'] == 'TAR':
      tar = tarfile.open(self.cfg.get('build')['base_url'])
      tmp_build_dir = '%s/%s/%s'  % (self.cfg.get('build')['tmpdir'], self.__BUILD_DIRECTORY_NAME, self.cfg.get('build')['base_url'])
      os.mkdirs(tmp_build_dir)
      tar.extractall(tmp_build_dir) 

  def create(self, node): pass

  def delete(self, node): pass

  def build(self, name):
    print 'build', name
    self.cfg = config.Config('%s/config.yaml' % (name) )
    self.download_base()

  def register(self): pass

  def app(self, name):
    try:
      os.mkdir(name)
      f = open('%s/config.yaml' % (name), 'w')
      f.close()
    except Exception, e: pass

  def run(self, options):
    opts = ['create','delete','build','app']
    for opt in opts:
      if eval('options.%s' % opt):
        eval('self.%s("%s")' % (opt, options.name) )
