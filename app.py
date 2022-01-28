import asyncio

from bs4 import BeautifulSoup

from mp import Mp
from utils import markdown_to_html


async def main(publish=True):
    with open('data/md.md', encoding='utf-8') as f:
        markdown = f.read()

    # 处理 markdown
    html, metadata = markdown_to_html(markdown)
    async with Mp() as mp:
        # 图片上传到微信
        soup = BeautifulSoup(html, 'lxml')
        queue = {}  # {origin_src: [img1, img2]}
        for img in soup.find_all('img'):
            src = img['src']
            if src in queue:
                queue[src].append(img)
            else:
                queue[src] = [img]
        results = await asyncio.gather(*[mp.upload_image(i) for i in queue.keys()])
        for i, origin_src in enumerate(queue):
            for img in queue[origin_src]:
                img['src'] = results[i] or origin_src
        html = str(soup)
        # 上传草稿
        media_id = await mp.upload_draft(
            title=metadata.get('title', '文章'),
            content=html,
            digest=metadata.get('abstract'),
        )
        return await mp.publish(media_id) if publish else media_id


if __name__ == '__main__':
    asyncio.run(main(publish=False), debug=True)
