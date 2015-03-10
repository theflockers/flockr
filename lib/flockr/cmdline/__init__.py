
import sys
from optparse import OptionParser

class CmdLine:

  options = None
  parser = None

  def __init__(self):

    self.parser = OptionParser()
    self.parser.add_option("-c", "--create", action="store_true", dest="create", help="create a new node")
    self.parser.add_option("-b", "--build", action="store_true", dest="build", help="build a image")
    self.parser.add_option("-d", "--delete", action="store_true", dest="delete", help="delete a node")
    self.parser.add_option("-a", "--app" action="store_true", dest="app", help="new application")

    (self.options, args) = self.parser.parse_args()

    if len(sys.argv) == 1:
      self.help()
      sys.exit(1)

  def get_options(self):
    return self.options

  def help(self):
    self.parser.print_help()


