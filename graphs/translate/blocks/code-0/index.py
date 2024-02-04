import base64
import re

from io import BytesIO
from lxml import etree
from google.cloud import translate
from ebooklib import epub, ITEM_DOCUMENT

def translate_html(client, contents, source_language_code, target_language_code) -> list[str]:
  project_id = "balmy-mile-348403"
  location = "global"
  parent = f"projects/{project_id}/locations/{location}"
  response = client.translate_text(
    request={
      "parent": parent,
      "contents": contents,
      "mime_type": "text/html",
      "source_language_code": source_language_code,
      "target_language_code": target_language_code,
    }
  )
  target_list = []
  for translation in response.translations:
    target_list.append(translation.translated_text)
  
  return target_list

def collect_child_text_list(dom):
  text_list = []
  child_doms = []

  for child_dom in dom.iterchildren():
    text = etree.tostring(child_dom, method="html", encoding="utf-8").decode("utf-8")
    text_list.append(text)
    child_doms.append(child_dom)
  
  return text_list, child_doms

def translate_content(client, page_content):
  parser = etree.HTMLParser(recover=True)

  # to remove <?xml version="1.0" encoding="utf-8"?> which lxml cannot parse
  xml = re.sub(r"^<\?xml.*\?>", "", page_content)
  # remove namespace of epub
  xml = re.sub(r"xmlns=\"http://www.w3.org/1999/xhtml\"", "", xml)
  xml = re.sub(r"xmlns:epub=\"http://www.idpf.org/2007/ops\"", "", xml)
  xml = re.sub(r"epub:", "", xml)

  root = etree.fromstring(xml, parser=parser)
  body_dom = root.find("body")

  merged_text_list = []
  source_text_list, child_doms = collect_child_text_list(body_dom)

  # TODO: 先这样
  source_text_list = source_text_list[:20]
  
  target_text_list = translate_html(
    client=client,
    contents=source_text_list,
    source_language_code="en",
    target_language_code="zh-CN",
  )
  for child_dom in child_doms:
    body_dom.remove(child_dom)

  for source, target in zip(source_text_list, target_text_list):
    source_dom = etree.fromstring(source, parser=parser)
    target_dom = etree.fromstring(target, parser=parser)
    body_dom.append(source_dom)
    body_dom.append(target_dom)

  return etree.tostring(root, method="html", encoding="utf-8").decode("utf-8")


def main(props, context):
  # https://cloud.google.com/translate/docs/advanced/translate-text-advance?hl=zh-cn
  client = translate.TranslationServiceClient()
  book = epub.read_epub(context.options["file"])

  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      content = item.get_content().decode("utf-8")
      content = translate_content(client, content)
      item.set_content(content)

  target_path = "/oomol-storage/books/target.epub"
  epub.write_epub(target_path, book, {})
  context.done()
