import re

from lxml import etree
from html import escape
from google.cloud import translate
from .group import ParagraphsGroup
from .utils import create_node

class _XML:
  def __init__(self, page_content: str, parser: etree.HTMLParser):
    regex = r"^<\?xml.*\?>"
    match = re.match(regex, page_content)
    xml = re.sub(regex, "", page_content)

    if match:
      self.head = match.group()
    else:
      self.head = ""

    self.root = etree.fromstring(xml, parser=parser)
    self.nsmap: dict = self.root.nsmap.copy()
    self.root.nsmap.clear()

  def encode(self) -> str:
    for key, value in self.nsmap.items():
      self.root.nsmap[key] = value

    text = etree.tostring(self.root, method="html", encoding="utf-8")
    text = text.decode("utf-8")

    # TODO: 替换成更完善的自闭检测
    # link 可能生成非自闭 tag，对 epub 是非法，此处用正则替换掉非自闭型
    text = re.sub(r"<((link|meta)[^>]*?)(?<!/)>", r"<\1/>", text)
    text = self.head + text

    return text

# https://cloud.google.com/translate/docs/advanced/translate-text-advance?hl=zh-cn
class Translator:
  def __init__(
    self, 
    project_id: str, 
    source_language_code: str, 
    target_language_code: str,
    max_paragraph_characters: int,
    clean_format: bool,
  ):
    self.client = translate.TranslationServiceClient()
    self.parser = etree.HTMLParser(recover=True)
    self.project_id = project_id
    self.source_language_code = source_language_code
    self.target_language_code = target_language_code
    self.max_paragraph_characters = max_paragraph_characters
    self.clean_format = clean_format

  def translate(self, text):
    translated_text_list = self._translate_by_google([text], "text/plain")
    if len(translated_text_list) > 0:
      return translated_text_list[0]
    else:
      return text

  def translate_page(self, page_content):
    xml = _XML(page_content, self.parser)
    source_text_list: list[str] = []

    for p_dom in xml.root.xpath('//p'):
      bin_text = etree.tostring(p_dom, method="html", encoding="utf-8")
      source_text_list.append(bin_text.decode("utf-8"))

    group = ParagraphsGroup(
      max_paragraph_len=self.max_paragraph_characters,
      # https://support.google.com/translate/thread/18674882/how-many-words-is-maximum-in-google?hl=en
      max_group_len=5000,
    )
    to_target_text_pair_map: dict[int, list[list[str]]] = {}

    for paragraph_list in group.split(source_text_list):
      source_text_list = list(map(lambda x: self._clean_p_tag(x.text), paragraph_list))
      target_text_list = self._translate_text_list(source_text_list)

      for i, target_text in enumerate(target_text_list):
        index = paragraph_list[i].index
        source_text = source_text_list[i]
        if self.clean_format:
          target_text = escape(target_text)
        else:
          target_text = self._clean_p_tag(target_text)

        pair = [source_text, target_text]

        if index in to_target_text_pair_map:
          # TODO: 判断是否有重复的 text 作为 debug
          to_target_text_pair_map[index].append(pair)
        else:
          to_target_text_pair_map[index] = [pair]

    for index, p_dom in enumerate(xml.root.xpath('//p')):
      new_p_doms = []
      for pair in to_target_text_pair_map[index]:
        for text in pair:
          new_p_dom = create_node(f"<p>{text}</p>", parser=self.parser)
          new_p_doms.append(new_p_dom)
  
      parent_dom = p_dom.getparent()
      index_at_parent = parent_dom.index(p_dom)

      for new_p_dom in reversed(new_p_doms):
        parent_dom.insert(index_at_parent, new_p_dom)
      parent_dom.remove(p_dom)

    return xml.encode()

  def _translate_text_list(self, source_text_list):
    target_text_list = [""] * len(source_text_list)
    to_translated_text_list = []
    index_list = []

    for index, text in enumerate(source_text_list):
      if text != "" and not re.match(r"[\s\n]+", text):
        text = f"<p>{text}</p>"
        if self.clean_format:
          dom = create_node(text, parser=self.parser)
          text = etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False)
          text = text.decode("utf-8")
        to_translated_text_list.append(text)
        index_list.append(index)
    
    if self.clean_format:
      mime_type = "text/plain"
    else:
      mime_type = "text/html"

    for i, text in enumerate(self._translate_by_google(to_translated_text_list, mime_type)):
      index = index_list[i]
      target_text_list[index] = text

    return target_text_list

    # body_dom = xml.root.find("body")
    # merged_text_list = []
    # source_text_list, child_doms = self._collect_child_text_list(body_dom)
    # source_text_groups = group.split(source_text_list)

    # for child_dom in child_doms:
    #   body_dom.remove(child_dom)

    # for index, source_text_list in enumerate(source_text_groups):   
    #   source_text_list = self._standardize_paragraph_list(source_text_list)
    #   target_text_list = self._translate_html(source_text_list)

    #   if index > 0:
    #     source_text_list.pop(0)
    #     target_text_list.pop(0)

    #   # 长度为 2 的数组来源于裁剪，不得已，此时它的后继的首位不会与它重复，故不必裁剪
    #   if index < len(source_text_groups) and len(source_text_list) > 2:
    #     source_text_list.pop()
    #     target_text_list.pop()

    #   for source, target in zip(source_text_list, target_text_list):
    #     source_dom = create_node(source, parser=self.parser)
    #     target_dom = create_node(target, parser=self.parser)

    #     if source_dom is not None and target_dom is not None:
    #       body_dom.append(source_dom)
    #       body_dom.append(target_dom)

  def _clean_p_tag(self, text: str) -> str:
    text = re.sub(r"^[\s\n]*<p[^>]*>", "", text)
    text = re.sub(r"</\s*p>[\s\n]*$", "", text)
    text = re.sub(r"[\s\n]+", " ", text)
    return text

  def _collect_child_text_list(self, dom):
    text_list = []
    child_doms = []

    for child_dom in dom.iterchildren():
      text = etree.tostring(child_dom, method="html", encoding="utf-8").decode("utf-8")
      text_list.append(text)
      child_doms.append(child_dom)
    
    return text_list, child_doms

  def _standardize_paragraph_list(self, text_list):
    target_list = []
    for text in text_list:
      text = re.sub(r"[\s\n]+", " ", text)
      if not re.match(r"^[\s\n]*<p.*>", text):
        text = "<p>" + text
      if not re.match(r"</\s*p>[\s\n]*$", text):
        text = text + "</p>"
      if text != "" and not re.match(r"[\s\n]+", text):
        target_list.append(text)
    return target_list

  def _translate_html(self, contents) -> list[str]:
    if self.clean_format:
      contents = contents.copy()
      for i, content in enumerate(contents):
        dom = create_node(content, parser=self.parser)
        contents[i] = etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False).decode("utf-8")

    if self.clean_format:
      target_list = self._translate_by_google(contents, "text/plain")
      for i, target_content in enumerate(target_list):
        target_list[i] = "<p>" + escape(target_content) + "</p>"
    else:
      target_list = self._translate_by_google(contents, "text/html")

    return target_list

  def _translate_by_google(self, source_text_list, mime_type) -> list[str]:
    indexes = []
    contents = []

    for index, source_text in enumerate(source_text_list):
      if source_text != "" and not re.match(r"^[\s\n]+$", source_text):
        indexes.append(index)
        contents.append(source_text)
    
    target_text_list = [""] * len(source_text_list)

    if len(contents) > 0:
      location = "global"
      parent = f"projects/{self.project_id}/locations/{location}"
      
      try:
        response = self.client.translate_text(
          request={
            "parent": parent,
            "contents": contents,
            "mime_type": mime_type,
            "source_language_code": self.source_language_code,
            "target_language_code": self.target_language_code,
          }
        )
      except Exception as e:
        print("translate contents failed:")
        for content in contents:
          print(content)
        raise e

      for i, translation in enumerate(response.translations):
        index = indexes[i]
        target_text_list[index] = translation.translated_text
    
    return target_text_list