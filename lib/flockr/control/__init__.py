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
from pprint import pprint
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
    lst = os.listdir('%s/root-fs' % self.tmp_build_dir)
    for l in lst:
      tar.add('%s/root-fs/%s' % (self.tmp_build_dir, l), arcname=l)

    tar.close()

  def deploy(self):
    # using CloudStack client because templates registration is not
    # covered by libcloud
    cfg        = self.main_cfg.get('production')
    deploy_cfg = self.cfg.get('deploy')

    self.api_url = cfg['url']
    self.api_key = cfg['apikey']
    self.secret  = cfg['secretkey']

    self.acs = CloudStack.Client(self.api_url, self.api_key, self.secret)

    # template name to be used
    tplname  = '%s:%s' % (self.appname, self.options.tplver )
    try:

      numnodes = 1
      if self.options.numnodes:
        numnodes = self.options.numnodes

      instsize = deploy_cfg['instance_size']
      if self.options.instsize:
        instsize = self.options.instsize

      for c in range(int(numnodes)):
        nodename  = '%s-%i' % (self.options.nodename, random.uniform(10,99))
        # Node definition
        nodeData = {
          'name': nodename,
          'displayname': nodename,
          'templateid': self.acs.listTemplates({'templatefilter': 'self', 'name': tplname})[0]['id'],
          'zoneid': deploy_cfg['zoneid'],
          'serviceofferingid': self.acs.listServiceOfferings({'name': instsize})[0]['id'],
          'securitygroupnames': deploy_cfg['security_groups'],
        }
        self.acs.deployVirtualMachine(nodeData)
      print colored('=> SUCCESS: %s nodes deployed' % numnodes, 'yellow')
    except Exception, e:
      print colored('=> ERROR:','yellow'), colored(str(e), 'red')


  def list(self): pass

  def delete(self): pass

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

  def node(self):
    # using CloudStack client because templates registration is not
    # covered by libcloud
    cfg = self.main_cfg.get('production')

    self.api_url = cfg['url']
    self.api_key = cfg['apikey']
    self.secret  = cfg['secretkey']

    self.acs = CloudStack.Client(self.api_url, self.api_key, self.secret)

    opts = ['list']
    for opt in opts:
      if eval('self.options.%s' % opt):
        eval('self.nd_%s()' % (opt))


  def tpl_register(self):

    self.tpl_upload()
    tplcfg = self.cfg.get('template')

    tpldata = {
      'name': '%s:%s' % (self.appname, self.options.tplver),
      'displaytext': '%s:%s' % (self.appname, self.options.tplver),
      'url': '%s/%s/app-%s.tar' % (tplcfg['display_url'], self.appname, self.appname),
      'format': tplcfg['format'],
      'hypervisor': tplcfg['hypervisor'],
      'requireshvm': str(tplcfg['hvm']),
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

  def nd_list(self):
    nds    = self.acs.listVirtualMachines({'templatefilter': 'self'})
    clist  = ['blue','cyan','white','magenta']
    cidx   = 0
    colord = {}
    for nd in nds:
#      pprint(nd)
      for key, val in nd.items():
        if not nd['templatedisplaytext'] in colord:
          colord[nd['templatedisplaytext']] = clist[cidx]
          cidx = cidx+1
        #print key, val
        if key == 'name':
          if re.match(self.appname, val):
            if re.match('.*Running$', nd['state']):
              color = 'green'
            else:
              color = 'red'

            print colored('=> %s (%s)' % (val,nd['serviceofferingname']), 'yellow'), colored('%s' % (nd['templatedisplaytext']), colord[nd['templatedisplaytext']]), colored('%s' % (nd['state']), color)

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
    opts = ['deploy','delete','build','app','template','node']
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
