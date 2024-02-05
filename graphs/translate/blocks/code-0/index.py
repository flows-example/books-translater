import base64

from io import BytesIO
from ebooklib import epub, ITEM_DOCUMENT
from logic.translator import Translator

def main(props, context):
  book = epub.read_epub(context.options["file"])
  translater = Translator(
    project_id="balmy-mile-348403",
    source_language_code="en",
    target_language_code="zh-CN",
  )
  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      content = item.get_content().decode("utf-8")
      content = translater.translate(content)
      item.set_content(content)

  bytes_io = BytesIO()
  epub.write_epub(bytes_io, book, {})
  base64_str = base64.b64encode(bytes_io.getvalue()).decode("utf-8")

  context.result(base64_str, "bin", True)
