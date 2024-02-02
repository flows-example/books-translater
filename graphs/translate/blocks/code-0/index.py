import requests

def main(props, context):
  # https://zhuanlan.zhihu.com/p/346484391
  url = 'http://translate.google.cn/translate_a/single?'
  param = 'client=at&sl=en&tl=zh-CN&dt=t&q=google'
  r = requests.get(url+param)
  context.result(props, "out", True)
