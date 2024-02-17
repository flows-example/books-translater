import io
import os
import time
import zipfile
import tempfile
import base64
import shutil

from logic import Translator, EpubContent

def main(props, context):
  translator = Translator(
    project_id="balmy-mile-348403",
    source_language_code=context.options["source"],
    target_language_code=context.options["target"],
    max_paragraph_characters=context.options.get("max_paragraph_characters", 800),
    clean_format=context.options["clean_format"],
  )
  file_path = context.options["file"]
  unzip_path = tempfile.mkdtemp()

  try:
    with zipfile.ZipFile(file_path, "r") as zip_ref:
      for member in zip_ref.namelist():
        target_path = os.path.join(unzip_path, member)
        if member.endswith("/"):
            os.makedirs(target_path, exist_ok=True)
        else:
          with zip_ref.open(member) as source, open(target_path, "wb") as file:
              file.write(source.read())

    _translate_folder(context, unzip_path, translator)
    in_memory_zip = io.BytesIO()

    with zipfile.ZipFile(in_memory_zip, "w") as zip_file:
      for root, _, files in os.walk(unzip_path):
        for file in files:
          file_path = os.path.join(root, file)
          relative_path = os.path.relpath(file_path, unzip_path)
          zip_file.write(file_path, arcname=relative_path)
          
    in_memory_zip.seek(0)
    zip_data = in_memory_zip.read()
    base64_str = base64.b64encode(zip_data).decode("utf-8")
    context.result(base64_str, "bin", True)

  finally:
    shutil.rmtree(unzip_path)

def _translate_folder(context, path: str, translator):
  epub_content = EpubContent(path)

  if "title" in context.options:
    book_title = context.options["title"]
  else:
    book_title = epub_content.title
    if not book_title is None:
      book_title += " - " + translator.translate([book_title])[0]

  if not book_title is None:
    epub_content.title = book_title

  authors = epub_content.authors
  to_authors = translator.translate(authors)

  for i, author in enumerate(authors):
    authors[i] = author + " - " + to_authors[i]

  epub_content.authors = authors

  for spine in epub_content.spines:
    if spine.media_type == "application/xhtml+xml":
      file_path = os.path.abspath(os.path.join(path, spine.href))
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = translator.translate_page(file_path, content)
      with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

  epub_content.save()