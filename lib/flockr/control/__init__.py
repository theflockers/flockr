#!/usr/bin/env python

from Queue import Queue
from threading import Thread
from termcolor import colored
from subprocess import Popen, call, PIPE

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
        print colored('=> Cleaning up tmpdir %s' % (self.tmp_build_dir), 'yellow')
        shutil.rmtree(self.tmp_build_dir)
        os.makedirs(root_fs)
      except Exception, e:
        print str(e)

      print colored('=> Extracting Base S.O. files to %s' % (root_fs), 'yellow')
      tar.extractall(root_fs)

  def clone_application(self):
    app_dir = '%s/app' % self.tmp_build_dir
    print colored('=> Fetching application from %s' % (self.cfg.get('build')['application_repository']), 'yellow')
    p = Popen(['/usr/bin/git','clone', self.cfg.get('build')['application_repository'], app_dir], stderr=PIPE, stdout=PIPE)
    p.wait()
    res = p.communicate()
    if len(res[1]) != 0:
      print colored('=> ERROR:', 'yellow'), colored('%s' % ( res[1] ), 'red')
    else:
      print colored('=> %s ' % (res[0].strip()), 'yellow')

  def merge_application(self):
    wwwroot = '%s/root-fs/%s' % ( self.tmp_build_dir, self.cfg.get('build')['application_wwwroot'] )
    srcdir  = '%s/app/' % (self.tmp_build_dir)
    print colored('=> Merging %s with base s.o. into %s' % (srcdir, wwwroot),'yellow')
    try:
      shutil.rmtree(wwwroot)
    except OSError, e:
      print colored('=> WARNING:', 'yellow'), colored('%s' % ( str(e) ), 'red')

    shutil.copytree(srcdir, wwwroot)

  def create_archive(self):
    print colored('=> Creating archive %s/app-%s.tar' % (self.name, self.name),'yellow')
    tar = tarfile.open('%s/app-%s.tar' %  (self.name, self.name), 'w:' )
    for root, dirs, files in os.walk('%s/root-fs' % self.tmp_build_dir ):
      for f in files:
        filepath =  "%s/%s" % (root,f)
        arcname =  re.sub('%s/root-fs/' % self.tmp_build_dir, '', filepath)
        if re.search('.git\/', root):
          continue
        tar.add('%s/%s' % (root, f), arcname = arcname)
    tar.close()

  def create(self, node): pass

  def delete(self, node): pass

  def build(self, name):
    # opening config
    self.name = name
    self.cfg = config.Config('%s/config.yaml' % (self.name) )

    self.tmp_build_dir = '%s/%s'  % (self.cfg.get('build')['tmpdir'], \
        self.__BUILD_DIRECTORY_NAME)

    print colored( '\n* Building app %s *\n' % self.name, 'yellow')
    self.download_base_system()
    self.clone_application()
    self.merge_application()
    self.create_archive()

    print colored('\n+++ Build done. Now you may want register a template +++\n', 'green')

  def register(self): pass

  def app(self, name):
    try:
      os.mkdir(name)
      f = open('%s/config.yaml' % (name), 'w')
      f.write(open('lib/flockr/example/config.yaml-example','r').read())
      f.close()
    except Exception, e: pass

  def run(self, options):
    opts = ['create','delete','build','app']
    for opt in opts:
      if eval('options.%s' % opt):
        eval('self.%s("%s")' % (opt, options.name) )
