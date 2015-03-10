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
