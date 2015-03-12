#!/usr/bin/env python

import CloudStack
from Queue import Queue
from threading import Thread
from termcolor import colored
from subprocess import Popen, call, PIPE

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


import os, sys, re
import shutil
import urllib,requests
import tarfile
import random, time
import magic

import flockr.config as config

class Control:

  __BUILD_DIRECTORY_NAME = 'flockr-build'

  cfg = None
  main_cfg = None

  def __init__(self, cfg):
    self.main_cfg = cfg

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
    if self.cfg.get('build')['repository_type'] == 'GIT':
      p = Popen(['/usr/bin/git','clone', self.cfg.get('build')['application_repository'], app_dir], stderr=PIPE, stdout=PIPE)
      p.wait()
      res = p.communicate()
      if len(res[1]) != 0:
        print colored('=> ERROR:', 'yellow'), colored('%s' % ( res[1] ), 'red')
      else:
        print colored('=> %s ' % (res[0].strip()), 'yellow')
    elif self.cfg.get('build')['repository_type'] == 'TAR':
      src = urllib.urlretrieve(self.cfg.get('build')['application_repository'], '%s/%s.tar' % (self.tmp_build_dir, self.appname ) )
      tar = tarfile.open(src[0])
      tar.extractall(app_dir)

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
    print colored('=> Creating archive %s/app-%s.tar' % (self.appname, self.appname),'yellow')
    tar = tarfile.open('%s/app-%s.tar' %  (self.appname, self.appname), 'w:' )
    for root, dirs, files in os.walk('%s/root-fs' % self.tmp_build_dir ):
      for f in files:
        filepath =  "%s/%s" % (root,f)
        arcname =  re.sub('%s/root-fs/' % self.tmp_build_dir, '', filepath)
        if re.search('.git\/', root):
          continue
        tar.add('%s/%s' % (root, f), arcname = arcname)
    tar.close()

  def create(self, node): pass

  def list(self): pass

  def delete(self, node): pass

  def build(self):
    self.tmp_build_dir = '%s/%s'  % (self.cfg.get('build')['tmpdir'], \
        self.__BUILD_DIRECTORY_NAME)

    print colored( '\n* Building app %s *\n' % self.appname, 'yellow')
    self.download_base_system()
    self.clone_application()
    self.merge_application()
    self.create_archive()

    print colored('\n+++ Build done. Now you may want to register a template +++\n', 'green')

  def template(self):
    # using CloudStack client because templates registration is not
    # covered by libcloud
    cfg = self.main_cfg.get('production')

    self.api_url = cfg['url']
    self.api_key = cfg['apikey']
    self.secret  = cfg['secretkey']

    self.acs = CloudStack.Client(self.api_url, self.api_key, self.secret)

    opts = ['register','list']
    for opt in opts:
      if eval('self.options.%s' % opt):
        eval('self.tpl_%s()' % (opt))

  def tpl_register(self):

    self.tpl_upload()
    tplcfg = self.cfg.get('template')

    tpldata = {
      'name': '%s:%s' % (self.appname, self.options.tplname),
      'displaytext': '%s:%s' % (self.appname, self.options.tplname),
      'url': '%s/%s/app-%s.tar' % (tplcfg['display_url'], self.appname, self.appname),
      'format': tplcfg['format'],
      'hypervisor': tplcfg['hypervisor'],
      'hvm': str(tplcfg['hvm']),
      'ostypeid': tplcfg['ostypeid'],
      'zoneid': tplcfg['zoneid'],
    }
    try:
      self.acs.registerTemplate(tpldata)
      print colored('=> Template %s created' % (tpldata['name']),'yellow'), colored('\n++ TIP: Use --list to see if is it ready ++', 'green')
    except Exception, e:
      print colored('=> ERROR:', 'yellow'), colored(str(e), 'red')

  def tpl_upload(self):
    upload_file_path = '%s/app-%s.tar' % (self.appname, self.appname)
    upload_url  = self.cfg.get('template')['upload_url']
    upload_file_params = {'file': upload_file_path }

    m = magic.open(magic.MIME_TYPE)
    m.load()

    try:
      res = requests.put('%s/%s' % (upload_url, upload_file_path),
          headers={'content-type': m.file(upload_file_path)},
          params=upload_file_params,
          data=open(upload_file_path).read())
    except Exception, e:
      print colored('=> ERROR:','yellow'), colored(str(e), 'red')

  def tpl_list(self):
    tpls = self.acs.listTemplates({'templatefilter': 'self'})
    for tpl in tpls:
      for key, val in tpl.items():
        #print key, val
        if key == 'name':
          if re.match(self.appname, val):
            if re.match('.*Complete$', tpl['status']):
              color = 'green'
            else:
              color = 'red'

            print colored('=> %s' % val, 'yellow'), colored('%s' % (tpl['status']), color)

  def app(self):
    if self.appname == 'None':
      print colored('=> ERROR: ', 'yellow'), colored('Missing application name', 'red')
      return 0

    try:
      os.mkdir(self.appname)
      f = open('%s/config.yaml' % (self.appname), 'w')
      f.write(open('/usr/share/flockr/example/config.yaml-example','r').read())
      f.close()
    except Exception, e: pass

  def run(self, options):
    opts = ['create','delete','build','app','template']
    self.options = options
    self.appname = options.appname

    if options.appname == None and options.app:
      print colored('=> ERROR: ', 'yellow'), colored('Missing application name', 'red')
      return 0

    for opt in opts:
      if eval('options.%s' % opt):
        if opt != 'app':
          self.cfg = config.Config('%s/config.yaml' % (options.appname) )
        eval('self.%s()' % (opt) )
