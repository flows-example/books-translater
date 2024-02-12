import base64

from io import BytesIO
from ebooklib import epub, ITEM_DOCUMENT, ITEM_STYLE
from logic import Translator

def main(props, context):
  # https://github.com/aerkalov/ebooklib/blob/master/README.md

  translator = _create_translater(context)
  origin_book = epub.read_epub(context.options["file"])
  book = epub.EpubBook()

  # set metadata
  book.set_identifier("id123456")
  book.set_title("Sample book")
  book.set_language("en")

  book.add_author("Author Authorowski")
  book.add_author(
      "Danko Bananko",
      file_as="Gospodin Danko Bananko",
      role="ill",
      uid="coauthor",
  )
  # add default NCX and Nav file
  # book.add_item(epub.EpubNcx())
  # book.add_item(epub.EpubNav())

  # define CSS style
  # style = "BODY {color: white;}"
  # nav_css = epub.EpubItem(
  #     uid="style_nav",
  #     file_name="style/nav.css",
  #     media_type="text/css",
  #     content=style,
  # )
  # # add CSS file
  # book.add_item(nav_css)

  book.toc = origin_book.toc
  book.spine = origin_book.spine

  for item in origin_book.items:
    if item.get_type() == ITEM_DOCUMENT:
      content = item.get_content().decode("utf-8")
      print(">>>", item.file_name)
      if "titlepage.xhtml" == item.file_name:
        print(content)
    book.add_item(item)

  # define Table Of Contents
  # book.toc = (
  #     epub.Link("chap_01.xhtml", "Introduction", "intro"),
  #     (epub.Section("Simple book"), (first_chapter,)),
  # )


  # first_chapter = None

  # for item in _get_items(translator, origin_book):
  #   if item.get_type() == ITEM_DOCUMENT:
  #     first_chapter = item
  #   book.add_item(item)

  # basic spine
  # book.spine = ["nav", first_chapter]

  # if "title" in context.options:
  #   new_book.set_title(context.options["title"])
  # else:
  #   new_book.set_title(translator.translate(book.title))

  # for author in book.get_metadata("DC", "creator"):
  #   new_book.add_author(author)

  _output_book(context, book)

def _create_translater(context) -> Translator:
  return Translator(
    project_id="balmy-mile-348403",
    source_language_code=context.options["source"],
    target_language_code=context.options["target"],
    max_paragraph_characters=context.options.get("max_paragraph_characters", 800),
    clean_format=context.options["clean_format"],
  )

def _get_items(translater: Translator, book):
  items = []
  
  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      content = item.get_content().decode("utf-8")
      content = translater.translate_page(content)
      new_item = epub.EpubHtml(
        title=item.title, 
        file_name=item.file_name, 
        lang=item.lang,
        content=content,
      )
      items.append(new_item)

    elif item.get_type() == ITEM_STYLE:
      content = item.get_content().decode("utf-8")
      new_item = epub.EpubItem(
        media_type=item.media_type,
        file_name=item.file_name, 
        content=content,
      )
      items.append(new_item)
    
  return items

def _output_book(context, book):
  bytes_io = BytesIO()
  epub.write_epub(bytes_io, book, {})
  base64_str = base64.b64encode(bytes_io.getvalue()).decode("utf-8")

  context.result(base64_str, "bin", True)