import asyncio
import random
import time
import uuid
from typing import Union

import httpx
import orjson

from config import APP_ID, APP_SECRET, AUTHOR
from config import db
from utils import preprocess_image

BASE_URL = 'https://api.weixin.qq.com/cgi-bin'

# def repeated_login(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         time.sleep(0.15)  # 暂停一段时间，防止系统检测异常（间隔为 0.1s 会报 “请不要过快点击” ）
#         r = func(*args, **kwargs)
#
#         # arg[0]是self，arg[1]是url
#         args = list(args)
#         args[1] = new_url
#         return func(*args, **kwargs)
#
#
#     return wrapper

MAX_RETRIES = 5


class AsyncClient(httpx.AsyncClient):
    async def _retry(self, *args, **kwargs):
        for i in range(MAX_RETRIES):
            try:
                r = await super().request(*args, **kwargs)
            except httpx.HTTPError:
                if i == MAX_RETRIES:
                    raise httpx.HTTPError
                print(f'[W] Network error, retrying...[{i + 1}/{MAX_RETRIES}]')
                continue
            else:
                return r

    async def request(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = orjson.dumps(kwargs['json'])
            del kwargs['json']
        r = await self._retry(*args, **kwargs)
        if r.json().get('errcode') == 40001:
            self.params['access_token'] = await update_access_token()
            return await self._retry(*args, **kwargs)
        return r


class Mp:
    def __init__(self):
        self.c = None

    @property
    async def access_token(self):
        access_token = db.get('access_token', '')
        expires = db.get('access_token_expires', time.time())
        if not access_token or expires - time.time() < 600:
            return await update_access_token()
        else:
            return access_token

    @property
    async def default_cover_image(self) -> dict:
        """
        [{'media_id': media_id, 'url': url}]
        """
        array = db.get('default_cover_image', [])
        if not array:
            array = await self.list_materials()
            assert len(array) > 0, '至少需要先上传一张图片'
            db.set('default_thumb_media_id', array)
        return random.choice(array)

    async def _create_client(self):
        return AsyncClient(
            base_url=BASE_URL,
            params={'access_token': await self.access_token}
        )

    @classmethod
    async def create(cls):
        self = Mp()
        self.c = await self._create_client()
        return self

    async def __aenter__(self):
        self.c = await self._create_client()
        return self

    async def __aexit__(self, *args):
        await self.c.aclose()

    async def upload_material(self, file: bytes, file_type='image', mime='jpeg'):
        r = await self.c.post(
            '/material/add_material',
            params={'type': file_type},
            files={'media': (f'{uuid.uuid4()}.{mime}', file)}
        )
        r = r.json()
        if 'url' not in r:
            print('[W] 素材上传失败', r.get('errmsg'))
        return r.get('url')

    async def upload_image(self, image: Union[bytes, str]):
        # to bytes
        if isinstance(image, str):
            if image.startswith('http'):
                async with httpx.AsyncClient() as c:
                    r = await c.get(image)
                    image = r.content
            else:
                with open(image, 'rb') as f:
                    image = f.read()
        image, mime = preprocess_image(image)
        return await self.upload_material(image, mime=mime)

    async def list_materials(self, mime_type='image', offset=0, count=20):
        r = await self.c.post('/material/batchget_material', json={
            'type': mime_type,
            'offset': offset,
            'count': count
        })
        r = r.json()
        print(r.get('errmsg', ''))
        return r.get('item')

    async def upload_draft(
            self,
            title: str,
            html: str,
            thumb_media_id: str,
            digest=None,
            author=None,
            source_url=None) -> str:
        data = {
            'title': title,
            'content': html,
            'thumb_media_id': thumb_media_id,
            'author': author or AUTHOR,
            'digest': digest,
            'content_source_url': source_url
        }
        r = await self.c.post('/draft/add', json={'articles': [data]})
        r = r.json()
        print(r.get('errmsg', ''))
        return r.get('media_id')

    async def hypocritical_publish(self, media_id: str) -> bool:
        # "发布"
        r = await self.c.post('/freepublish/submit', json={
            'media_id': media_id
        })
        r = r.json()
        if r.get('errcode') != 0:
            print(r.get('errmsg'))
        return r.get('errcode') == 0

    async def publish(self, media_id: str) -> bool:
        # "群发"
        r = await self.c.post('/message/mass/sendall', json={
            'filter': {'is_to_all': True},
            'mpnews': {'media_id': media_id},
            'msgtype': 'mpnews',
            'send_ignore_reprint': 1
        })
        r = r.json()
        if r.get('errcode') != 0:
            print(r.get('errmsg'))
        return r.get('errcode') == 0


async def update_access_token() -> str:
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.get('/token', params={
            'grant_type': 'client_credential',
            'appid': APP_ID,
            'secret': APP_SECRET
        })
    r = r.json()
    access_token = r.get('access_token')
    assert access_token, f'Update access token failed {r.get("errmsg")}'
    db.set('access_token', access_token)
    db.set('access_token_expires', time.time() + r.get('expires_in', 0))
    return access_token


async def debug():
    async with Mp() as mp:
        print(await mp.default_cover_image)


if __name__ == '__main__':
    asyncio.run(debug(), debug=True)
