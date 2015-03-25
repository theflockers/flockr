
import sys
from optparse import OptionParser,OptionGroup

class CmdLine:

  options = None
  parser = None

  def __init__(self):

    self.parser = OptionParser()

    application = OptionGroup(self.parser, "Application Options")
    application.add_option("-a", "--create", action="store", dest="application", help="new application")
    application.add_option("-p", "--application-name", action="store", dest="appname", help="application name")

    operation = OptionGroup(self.parser, "General Options")
    operation.add_option("-d", "--destroy", action="store_true", dest="destroy", help="destroy a node or template")

    operation.add_option("-f", "--force", action="store_true", dest="force", help="force destroy")
    operation.add_option("-l", "--list", action="store_true", dest="list", help="list nodes|templates (requires -t/-n)")
    #self.parser.add_option("--node-name", action="store", dest="nodename", help="node name")
    #self.parser.add_option("--num-nodes", action="store", dest="numnodes", help="number of nodes to deploy")
    operation.add_option("-v","--template-version", action="store", dest="tplver", help="template name to create/list/destroy (requires -t/-n)")

    template = OptionGroup(self.parser, "Template Options")
    template.add_option("-t", "--template", action="store_true", dest="template", help="template")
    template.add_option("-r", "--register", action="store_true", dest="register", help="register a template (requires -t/--template option)")

    node = OptionGroup(self.parser, "Node Options")
    node.add_option("-n", "--node", action="store_true", dest="node", help="node")
    node.add_option("-c", "--deploy", action="store_true", dest="deploy", help="deploy a new node")
    node.add_option("-e","--node-name", action="store", dest="nodename", help="node name")
    node.add_option("-m","--num-nodes", action="store", dest="numnodes", help="number of nodes to deploy")
    node.add_option("-s", "--instance-size", action="store", dest="instsize", help="instance size (overrides config)")

    build = OptionGroup(self.parser, "Build Options")
    build.add_option("-b", "--build", action="store_true", dest="build", help="build a image")
    build.add_option("-y", "--build-type", action="store", dest="buildtype", help="build type (vhd, lxc)")

    self.parser.add_option_group(application)
    self.parser.add_option_group(build)
    self.parser.add_option_group(node)
    self.parser.add_option_group(template)
    self.parser.add_option_group(operation)

    (self.options, args) = self.parser.parse_args()

    if len(sys.argv) == 1:
      self.help()
      sys.exit(1)

  def get_options(self):
    return self.options

  def help(self):
    self.parser.print_help()


