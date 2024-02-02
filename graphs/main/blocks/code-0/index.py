from ebooklib import epub, ITEM_DOCUMENT

def main(props, context):
  book = epub.read_epub(context.options["file"])
  result = book.title
  context.result(book.title, "title", False)
  count = 0

  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      count += 1
      if count == 3:
        context.result(item.get_name(), "page_name", False)
        context.result(item.get_content().decode("utf-8"), "page_content", False)
        break

  context.done()
