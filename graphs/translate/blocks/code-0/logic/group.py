from .paragraph_sliter import split_paragraph

class Paragraph:
  def __init__(self, text: str, index: int):
    self.text: str = text
    self.index: int = index

class ParagraphsGroup:
  def __init__(self, max_paragraph_len: int, max_group_len: int):
    self.max_paragraph_len: int = max_paragraph_len
    self.max_group_len: int = max_group_len

  def split(self, text_list: list[str]) -> list[list[Paragraph]]:
    splited_paragraph_list: list[Paragraph] = []

    for index, text in enumerate(text_list):
      if len(text) > self.max_paragraph_len:
        for cell in split_paragraph(text):
          while len(cell) > self.max_group_len:
            splited_paragraph_list.append(Paragraph(
              text=cell[:self.max_group_len], 
              index=index,
            ))
            cell = cell[self.max_group_len:]
          if len(cell) > 0:
            splited_paragraph_list.append(Paragraph(cell, index))

    sum_len = 0
    self_paragraphs_count = 0
    grouped_paragraph_list: list[list[Paragraph]] = []
    current_paragraph_list: list[Paragraph] = []

    for paragraph in splited_paragraph_list:
      if len(current_paragraph_list) > 0 and sum_len + len(paragraph.text) > self.max_group_len:
        grouped_paragraph_list.append(current_paragraph_list)
        sum_len = 0
        self_paragraphs_count = 0

        # 确保分组中有首尾 2 段分别与上一组、下一组重复，以让翻译具有一定上下文，增强翻译准确性
        if len(current_paragraph_list) <= 2:
          current_paragraph_list = []
        else:
          current_paragraph_list = current_paragraph_list[-2:]
          for cell in current_paragraph_list:
            sum_len += len(cell.text)

      sum_len += len(paragraph.text)
      self_paragraphs_count += 1
      current_paragraph_list.append(paragraph)

    if self_paragraphs_count > 0:
      grouped_paragraph_list.append(current_paragraph_list)

    return grouped_paragraph_list
