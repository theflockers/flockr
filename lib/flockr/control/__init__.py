#!/usr/bin/env python

import CloudStack
from Queue import Queue
from threading import Thread
from termcolor import colored, cprint
from subprocess import Popen, call, PIPE, STDOUT

import imp
import os, sys, re
import shutil, shlex
import urllib,requests
import tarfile, tempfile
from pprint import pprint
from contextlib import closing
import random, time
import magic

import flockr.config as config

class Control:

  __BUILD_DIRECTORY_NAME = 'flockr-build'

  cfg           = None
  main_cfg      = None

  __output      = True
  __already_off = False

  __SITE__      =  imp.find_module('flockr')[1]

  def __init__(self, cfg):
    self.main_cfg = cfg

  def download_base_system(self):
    print colored('Base S.O. archive format:', 'yellow'), colored(self.cfg.get('build')['base_format'], 'green')
    print
    if self.cfg.get('build')['base_format'] == 'TAR':
      src = urllib.urlretrieve(self.cfg.get('build')['base_url'])
      #tmp = tempfile.NamedTemporaryFile(delete=False)
      #with closing(requests.get(self.cfg.get('build')['base_url'], stream=True)) as r:
      #  tmp.write(r.content)
      #  tmp.flush()
      #tmp.close()
      #tar = tarfile.open(tmp.name)
      try:
        tar = tarfile.open(src[0])
        root_fs = '%s/root-fs' % (self.tmp_build_dir)
        print colored('=> Cleaning up tmpdir %s' % (self.tmp_build_dir), 'yellow')
        shutil.rmtree(self.tmp_build_dir)
        os.makedirs(root_fs)
        print colored('=> Extracting Base S.O. files to %s' % (root_fs), 'yellow')
        tar.extractall(root_fs)
      except Exception, e:
        print str(e)

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

    shutil.copytree(srcdir, wwwroot, symlinks=True)

  def create_archive(self):
    print colored('=> Creating archive %s/%s.tar' % (self.appname, self.appname),'yellow')

    tplcfg = self.cfg.get('template')
    tplext = tplcfg['format'].lower()

    if tplcfg['isextractable']:
      tplext = '%s.gz' % tplext

    tar = tarfile.open('%s/%s.%s' %  (self.appname, self.appname, tplext), 'w:gz' )
    lst = os.listdir('%s/root-fs' % self.tmp_build_dir)
    for l in lst:
      tar.add('%s/root-fs/%s' % (self.tmp_build_dir, l), arcname=l)

    tar.close()

  def create_image(self):
    root_fs = '%s/root-fs' % self.tmp_build_dir
    p = Popen(['genisoimage','-f','-r','-o','/tmp/flockr-build/%s.iso' % (self.appname), root_fs], stderr=STDOUT, stdout=PIPE)
    res = p.communicate()
    eval('self.create_%s()' % (self.options.buildtype))
    #print colored('=> ERROR:', 'yellow'), colored('%s' % ( res[0] ), 'red')

  def create_vhd(self):
    cmd = 'qemu-img convert -f host_cdrom -O vpc %s/%s.iso %s/%s.vhd' % (self.tmp_build_dir, self.appname, self.appname, self.appname)
    p = Popen(shlex.split(cmd),  stderr=PIPE, stdout=PIPE)
    p.wait()

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
        if not self.options.nodename:
          self.options.nodename = self.appname
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

  def build(self):
    self.tmp_build_dir = '%s/%s'  % (self.cfg.get('build')['tmpdir'], \
        self.__BUILD_DIRECTORY_NAME)

    if not self.options.buildtype:
      print colored( '* don\'t know what to build... use --build-type=[lxc|qcow2|vhd]', 'yellow')
      return

    print colored( '\n* Building app %s *\n' % self.appname, 'yellow')
    self.download_base_system()
    if self.cfg.get('build')['deploy_app']:
      self.clone_application()
      self.merge_application()

    if re.search('^lxc$', self.options.buildtype, re.IGNORECASE):
      self.create_archive()
    if re.search('^(vhd|qcow2)$', self.options.buildtype, re.IGNORECASE):
      self.create_image()

    print colored('\n+++ Build done. Now you may want to register a template +++\n', 'green')

  def template(self):
    # using CloudStack client because templates registration is not
    # covered by libcloud
    cfg = self.main_cfg.get('production')

    self.api_url = cfg['url']
    self.api_key = cfg['apikey']
    self.secret  = cfg['secretkey']

    self.acs = CloudStack.Client(self.api_url, self.api_key, self.secret)

    opts = ['register','list','destroy']
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

    opts = ['list','destroy']
    for opt in opts:
      if eval('self.options.%s' % opt):
        eval('self.nd_%s()' % (opt))


  def tpl_register(self):

    tplcfg = self.cfg.get('template')
    tplext = tplcfg['format'].lower()
    if tplcfg['isextractable']:
      tplext = '%s.gz' % tplext

    ostype = self.acs.listOsTypes({'description': tplcfg['ostype']})[0]
    if not ostype:
      return False

    if not self.tpl_upload():
      return False

    tpldata = {
      'name': '%s:%s' % (self.appname, self.options.tplver),
      'displaytext': '%s:%s' % (self.appname, self.options.tplver),
      'url': '%s/%s/%s.%s' % (tplcfg['display_url'], self.appname, self.appname, tplext),
      'format': tplcfg['format'],
      'hypervisor': tplcfg['hypervisor'],
      'requireshvm': str(tplcfg['hvm']),
      'ostypeid': ostype['id'],
      'zoneid': tplcfg['zoneid'],
      'passwordenabled': str(tplcfg['passwordenabled']),
      'isextractable': str(tplcfg['isextractable']),
    }
    try:
      self.acs.registerTemplate(tpldata)
      print colored('=> Template %s created' % (tpldata['name']),'yellow'), colored('\n++ TIP: Use --list to see if is it ready ++', 'green')
    except Exception, e:
      print colored('=> ERROR:', 'yellow'), colored(str(e), 'red')

  def tpl_upload(self):
    try:
      m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
      tplcfg = self.cfg.get('template')
      tplext = tplcfg['format'].lower()
      if tplcfg['isextractable']:
        tplext = '%s.gz' % tplext

      upload_file_path = '%s/%s.%s' % (self.appname, self.appname, tplext)
      upload_url  = self.cfg.get('template')['upload_url']
      upload_file_params = {'file': upload_file_path }

    except Exception, e:
      m.close()
      print 'could not upload template', str(e)
      return False

    try:
      res = requests.put('%s/%s' % (upload_url, upload_file_path),
          headers={'content-type': m.id_filename(upload_file_path)},
          params=upload_file_params,
          data=open(upload_file_path).read())
      m.close()

      return True

    except Exception, e:
      print colored('=> ERROR:','yellow'), colored(str(e), 'red')

  def tpl_list(self):

    args = {'templatefilter': 'self'}

    if self.options.tplver:
      args['name'] = '%s:%s' % (self.options.appname, self.options.tplver)

    tpls = self.acs.listTemplates(args)
    tpld =[]
    for tpl in tpls:
      for key, val in tpl.items():
        #print key, val
        if key == 'name':
          if re.match(self.appname, val):
            tpld.append(tpl)
            if re.match('.*Complete$', tpl['status']):
              color = 'green'
            else:
              color = 'red'

            if self.__output:
              print colored('=> %s' % val, 'yellow'), colored('%s' % (tpl['status']), color)

    return tpld

  def tpl_destroy(self):
    self.__output = False
    tpls = self.tpl_list()

    if tpls:
      print colored('\n*** Destroy template ***\n', 'red')
      for tpl in tpls:
        print colored('=> TEMPLATE: %s ' % tpl['name'],'yellow')

      names = []
      if self.options.force:
        for tpl in tpls:
          names.append(tpl['name'])
          self.acs.deleteTemplate({'id': tpl['id']})
      else:
        answ = raw_input(colored('\nAre you sure you want to destroy this template(s) [Yes|No]: ', 'white'))
        if re.search('^(y|yes)$', answ, re.IGNORECASE):
          for tpl in tpls:
            names.append(tpl['name'])
            self.acs.deleteTemplate({'id': tpl['id']})

          print colored('\n=> DESTROYED:', 'yellow'), colored(', '.join(map(str, names)), 'green')

  def nd_list(self, node=False):
    args = {'templatefilter': 'self'}
    # if node specified, override self.options.nodename
    if node:
      self.options.nodename = nodename
    if self.options.nodename:
      args['name'] = self.options.nodename
    if self.options.tplver:
      # turn off output just for this call
      if self.__output == False:
        self.__already_off = True
      else:
        self.__output = False
      args['templateid'] = self.tpl_list()[0]['id']
      # ok, display output again
      if not self.__already_off: self.__output = True
    # list
    nds    = self.acs.listVirtualMachines(args)

    clist  = ['blue','cyan','white','green','magenta','red']
    cidx   = 0
    colord = {}
    rnd    = []
    for nd in nds:
      #pprint(nd)
      for key, val in nd.items():
        if not nd['templatedisplaytext'] in colord:
          colord[nd['templatedisplaytext']] = clist[cidx]
          if cidx == len(clist)-1:
            cidx = 0
          else:
            cidx = cidx+1
        #print key, val
        if key == 'templatedisplaytext':
          if re.match(self.appname, val):
            rnd.append(nd)
            if re.match('.*Running$', nd['state']):
              color = 'green'
            else:
              color = 'red'

            if self.__output:
              print colored('=> %s (%s) (%s)' % (nd['name'],nd['serviceofferingname'], nd['nic'][0]['ipaddress']), 'yellow'), colored('%s' % (nd['templatedisplaytext']), colord[nd['templatedisplaytext']]), colored('%s' % (nd['state']), color)

    if not self.__output:
      return rnd


  def nd_destroy(self,node=False):
    # turn off output
    self.__output = False

    node = self.nd_list()
    if node:
      print colored('\n*** Destroy node ***\n', 'red')
      for n in node:
        print colored('=> NODE: %s ' % n['displayname'],'yellow')

      names = []
      if self.options.force:
        for n in node:
          names.append(n['name'])
          self.acs.destroyVirtualMachine({'id': n['id'], 'expunge': 'true'})
      else:
        answ = raw_input(colored('\nAre you sure you want to destroy this node(s) [Yes|No]: ', 'white'))
        if re.search('^(y|yes)$', answ, re.IGNORECASE):
          for n in node:
            names.append(n['name'])
            self.acs.destroyVirtualMachine({'id': n['id'], 'expunge': 'true'})

          print colored('\n=> DESTROYED:', 'yellow'), colored(', '.join(map(str, names)), 'green')


  def application(self):
    if not self.appname:
      print colored('=> ERROR: ', 'yellow'), colored('Missing application name', 'red')
      return 0

    try:

      os.mkdir(self.appname)
      f = open('%s/config.yaml' % (self.appname), 'w')
      f.write(open('%s/config.yaml-example' % self.__SITE__, 'r').read())
      f.close()
      print colored('=> CREATED: ', 'yellow'), colored('application %s' % self.appname, 'green')
    except Exception, e:
      print colored('=> ERROR: ', 'yellow'), colored(str(e), 'red')


  def run(self, options):

    opts = ['deploy','build','application','template','node']
    self.options = options

    if options.application and not options.appname:
      options.appname = options.application

    self.appname = options.appname

    ##if options.appname == None and options.app:
    ##  print colored('=> ERROR: ', 'yellow'), colored('Missing application name', 'red')
    #  return 0

    #for opt in opts:
    #  if sys.argv[1] not in opts:
    #    return False

    for opt in opts:
      if eval('options.%s' % opt):
        if opt != 'application':
          self.cfg = config.Config('%s/config.yaml' % (options.appname) )
        eval('self.%s()' % (opt) )
