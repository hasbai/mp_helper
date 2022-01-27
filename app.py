import asyncio
import os

import diskcache
from bs4 import BeautifulSoup

from mp import Mp

APP_ID = os.environ.get('MP_APP_ID')
APP_SECRET = os.environ.get('MP_APP_SECRET')
assert APP_ID, 'Environment variable MP_APP_ID must be set.'
assert APP_SECRET, 'Environment variable MP_APP_SECRET must be set.'

db = diskcache.Cache('data/db')


async def main():
    with open('data/content.html', encoding='utf-8') as f:
        content = f.read()

    async with Mp() as mp:
        # 图片上传到微信
        soup = BeautifulSoup(content, 'lxml')
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
        content = str(soup)
        # 上传草稿
        media_id = await mp.upload_draft('test', content)
        return await mp.publish(media_id)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
