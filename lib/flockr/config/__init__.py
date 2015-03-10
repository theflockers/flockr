import os,sys
import yaml


class Config:

  yaml_data = None

  def __init__(self):
    try:
      c = open('config.yaml','r')
      self.yaml_data = yaml.load(c.read())
    except Exception, e:
      print str(e)
      sys.exit(1)

  def get_data(self):
    print self.yaml_data

  def get(self, var):
    return self.yaml_data[var]
