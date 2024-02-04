from ebooklib import epub, ITEM_DOCUMENT

def main(props, context):
  book = epub.read_epub(context.options["file"])
  context.result(book.title, "title", False)
  pages = []

  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      pages.append({
        "name": item.get_name(),
        "content": item.get_content().decode("utf-8"),
      })

  pages = [pages[3]]

  context.result(pages, "pages", True)
