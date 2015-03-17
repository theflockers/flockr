
import sys
from optparse import OptionParser

class CmdLine:

  options = None
  parser = None

  def __init__(self):

    self.parser = OptionParser()
    self.parser.add_option("-c", "--deploy", action="store_true", dest="deploy", help="deploy a new node")
    self.parser.add_option("-b", "--build", action="store_true", dest="build", help="build a image")
    self.parser.add_option("-d", "--destroy", action="store_true", dest="destroy", help="destroy a node or template")
    self.parser.add_option("-a", "--create-app", action="store_true", dest="app", help="new application")
    self.parser.add_option("-t", "--template", action="store_true", dest="template", help="template")
    self.parser.add_option("-n", "--node", action="store_true", dest="node", help="node")
    self.parser.add_option("-r", "--register", action="store_true", dest="register", help="register a template (need -t --template option)")
    self.parser.add_option("-l", "--list", action="store_true", dest="list", help="list nodes|templates (need -t or --node")
    self.parser.add_option("--node-name", action="store", dest="nodename", help="node name")
    self.parser.add_option("--num-nodes", action="store", dest="numnodes", help="number of nodes to deploy")
    self.parser.add_option("--template-version", action="store", dest="tplver", help="template name to create")
    self.parser.add_option("--application-name", action="store", dest="appname", help="node or application name")
    self.parser.add_option("--instance-size", action="store", dest="instsize", help="instance size (overlap config)")

    (self.options, args) = self.parser.parse_args()

    if len(sys.argv) == 1:
      self.help()
      sys.exit(1)

  def get_options(self):
    return self.options

  def help(self):
    self.parser.print_help()


