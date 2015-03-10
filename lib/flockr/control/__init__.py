#!/usr/bin/env python

from Queue import Queue
from threading import Thread
from pprint import pprint

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import ConfigParser
import os, sys, re
import random, time

import flockr.config as config


class Control:

  def __init__(self):

  def create(self, node):

  def delete(self), node:

  def build(self):

  def register(self, template)

stime = time.time()
random.seed()

WORKER_THREADS = 10

# read config to init the script
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.readfp(open('%s/.cloudmonkey/config' % (os.environ['HOME'])))

username  = config.get('producao','username')
apikey    = config.get('producao','apikey')
secretkey = config.get('producao','secretkey')
url       = config.get('producao','url')

q = Queue()

cls = get_driver(Provider.CLOUDSTACK)

def create_node(node):

  driver = cls(key=apikey, secret=secretkey, url=url, secure=False)
  node = driver.create_node(name='%s-%i' % (node[0]['name'], random.randint(1,100)), image=node[0]['template'],
        ex_security_groups=node[0]['security_groups'], size=node[0]['service_offering'])

  print 'Time spent on creation: %f' % (time.time() - stime)
  print 'Node name: ', node.name

def destroy_node(node):
  driver = cls(key=apikey, secret=secretkey, url=url, secure=False)
  driver.destroy_node(node, ex_expunge=True)
  print "Time spent on delete node: %f" % ( time.time() - stime )
  print "Node name: ", node.name

def del_worker():
  while True:
    some = q.get()
    destroy_node(some);
    q.task_done()

def cre_worker():
  while True:
    some = q.get()
    create_node(some);
    q.task_done()

if __name__ == "__main__":

  if len(sys.argv) == 0:
      parser.print_help()
      sys.exit()

  if option.create:

    driver = cls(key=apikey, secret=secretkey, url=url, secure=False)
    node = {}
    # get the image name to deploy
    for image in driver.list_images():
      if image.name == option.template_name:
        node['template'] = image
        break

    if not node.get('template'):
      print "template %s does not exists...bye" % (option.template_name)
      sys.exit(1)

    # get service offering id
    for size in driver.list_sizes():
      if re.search (re.escape(option.service_offering.strip()), size.name):
        node['service_offering'] = size
        break

    node['security_groups'] = option.security_groups.split(",")
    node['name'] = option.node_name.strip()

    try:
      times    = int(option.num_nodes)
    except:
      times = 1

    print "\n**** DEPLOY *****\n\n"
    print "Creating %i hosts on live\n" % (option.nodes)
    print "Template: \033[30G%s" % (option.template_name)
    print "Instance: \033[30G%s" % (option.service_offering)
    print "Security Group:\033[30G%s\n\n" % (option.security_groups)


    for i in range(WORKER_THREADS):
      #print "Lauching worker %i" % (i)
      t = Thread(target=cre_worker)
      t.daemon = True
      t.start()

    for i in range(option.nodes):
      q.put( ( node, i) )

  elif option.delete:
    basename = option.node_name
    driver = cls(key=apikey, secret=secretkey, url=url, secure=False)

    for i in range(WORKER_THREADS):
      #print "Lauching worker %i" % (i)
      t = Thread(target=del_worker)
      t.daemon = True
      t.start()

    for node in driver.list_nodes():
      if re.search (basename, node.name):
        q.put(node)

  q.join()
