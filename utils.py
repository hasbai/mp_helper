import io
import re

import css_inline
import markdown2
from PIL import Image
from bs4 import BeautifulSoup
from markdown import Markdown

Image.MAX_IMAGE_PIXELS = None


def preprocess_image(image: bytes, size=10) -> tuple[bytes, str]:
    """
    Reformat image to jpeg and resize it if necessary.
    Args:
        image:
        size:
    Returns:

    """
    image_bytes = image
    image = Image.open(io.BytesIO(image_bytes))
    assert image.format in Image.MIME
    if len(image_bytes) < size * 1024 ** 2:
        return image_bytes, image.format.lower()
    # to jpeg and compress
    bytes_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(bytes_io, format='JPEG')
    image_size = bytes_io.tell() / 1024 ** 2
    if image_size > size:
        print(f'图片大小超过{size}M, 正在压缩')
        image = Image.open(bytes_io)
        w, h = image.size
        ratio = size / image_size
        w, h = int(w * ratio), int(h * ratio)
        image = image.resize((w, h), Image.ANTIALIAS)
    bytes_io = io.BytesIO()
    image.save(bytes_io, quality=85, optimize=True, format='JPEG')
    return bytes_io.getvalue(), 'jpeg'


def markdown_to_plain_text(content):
    def unmark_element(element, stream=None):
        if stream is None:
            stream = io.StringIO()
        if element.text:
            stream.write(element.text)
        for sub in element:
            unmark_element(sub, stream)
        if element.tail:
            stream.write(element.tail)
        return stream.getvalue()

    # patching Markdown
    Markdown.output_formats["plain"] = unmark_element
    # noinspection PyTypeChecker
    md = Markdown(output_format="plain")
    md.stripTopLevelTags = False

    # 该方法会把 ![text](url) 中的 text 丢弃，因此需要手动替换
    content = re.sub(r'!\[(.+)]\(.+\)', r'\1', content)

    return md.convert(content)


def get_abstract(markdown: str) -> tuple[str, str]:
    """
    返回 去除摘要的 markdown 和 摘要
    """
    pattern = r'(---[\s\S]+---)([\s\S]+)<!-- more -->'
    li = re.findall(pattern, markdown)
    if not li or len(li[0]) < 2:
        return markdown, ''
    abstract = markdown_to_plain_text(li[0][1].strip())
    markdown = markdown.replace(f'{li[0][1]}<!-- more -->', '')
    return markdown, abstract


def markdown_to_html(content: str, debug=False) -> tuple[str, dict]:
    content, abstract = get_abstract(content)
    html = markdown2.markdown(content, extras=[
        'metadata', 'cuddled-lists', 'code-friendly', 'fenced-code-blocks', 'footnotes',
        'tables', 'task_list', 'strike', 'pyshell'
    ])
    metadata = html.metadata
    metadata['abstract'] = abstract.strip()
    soup = BeautifulSoup(html, 'lxml')
    # 图片注释
    for img in soup.select('img'):
        parent = img.parent
        parent.append(img.get('alt', ''))
        parent['class'] = 'img-alt'
    # 插入 参考资料 标签
    footnotes = soup.select_one('.footnotes')
    if footnotes:
        tag = soup.new_tag('h3')
        tag.string = '参考资料'
        footnotes.insert(0, tag)
        footnotes.select_one('hr').extract()
    html = f'''
    <h1>{metadata.get('title')}</h1>
    <div class="abstract">{abstract}</div>
    {str(soup).replace('codehilite', 'highlight')}
    <link rel="stylesheet" type="text/css" href="css/wechat.css">
    '''
    if debug:
        css = '<link rel="stylesheet" type="text/css" href="../css/wechat.css">'
        html = css + html
    else:
        html = css_inline.inline(html)

    return html, metadata


if __name__ == '__main__':
    with open('data/1.md', 'r', encoding='utf-8') as f:
        html = markdown_to_html(f.read(), debug=False)
    with open('data/html.html', 'w', encoding='utf-8') as f:
        f.write(html[0])
