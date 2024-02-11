from lxml import etree

def create_node(node_str: str, parser):
  return etree.HTML(node_str, parser=parser).find("body/*")