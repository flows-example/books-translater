import re
from lxml import etree



def main(props, context):
  # to remove <?xml version="1.0" encoding="utf-8"?> which lxml cannot parse
  xml = re.sub(r"^<\?xml.*\?>", "", props["xml"])
  # remove namespace of epub
  xml = re.sub(r"xmlns=\"http://www.w3.org/1999/xhtml\"", "", xml)
  xml = re.sub(r"xmlns:epub=\"http://www.idpf.org/2007/ops\"", "", xml)
  xml = re.sub(r"epub:", "", xml)

  root = etree.fromstring(xml)
  paras = root.findall(f"body/p")

  for para in paras:
    para_texts = []
    for child in para.iterchildren():
      text = etree.tostring(child, method="html", encoding="utf-8").decode("utf-8")
      para_texts.append(text)
    para_text = "".join(para_texts)
    print(para_text)

  context.done()