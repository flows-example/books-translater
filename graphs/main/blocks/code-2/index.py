from ebooklib import epub

def main(props, context):
  book = epub.EpubBook()
  book.set_title(props["title"])
  book.add_author("moskize")

  for page in props["pages"]:
    name = page["name"]
    content = page["content"]
    chapter = epub.EpubHtml(title=name, file_name=name, lang="zh-CN")
    chapter.set_content(content)
    book.add_item(chapter)

  epub.write_epub(context.options["file"], book, {})
  context.done()
