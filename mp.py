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


class AsyncClient(httpx.AsyncClient):
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = orjson.dumps(kwargs['json'])
            del kwargs['json']
        return super().post(*args, **kwargs)


class Mp:
    def __init__(self):
        self.c = None

    @property
    async def access_token(self):
        access_token = db.get('access_token', '')
        expires = db.get('access_token_expires', time.time())
        if not access_token or expires - time.time() < 600:
            return await self.update_access_token()
        else:
            return access_token

    @property
    async def default_thumb_media_id(self):
        i = db.get('default_thumb_media_id', '')
        if not i:
            array = await self.list_materials()
            assert len(array) > 0, '至少需要先上传一张图片'
            i = array[0]['media_id']
            db.set('default_thumb_media_id', i)
        return i

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

    async def update_access_token(self) -> str:
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

    async def upload_draft(self, title: str, content: str, digest=None, author=None, source_url=None,
                           thumb_media_id=None) -> str:
        thumb_media_id = thumb_media_id or await self.default_thumb_media_id
        data = {
            'title': title,
            'content': content,
            'thumb_media_id': thumb_media_id,
            'author': author or AUTHOR,
            'digest': digest,
            'content_source_url': source_url
        }
        r = await self.c.post('/draft/add', json={'articles': [data]})
        r = r.json()
        print(r.get('errmsg', ''))
        return r.get('media_id')

    async def publish(self, media_id: str) -> bool:
        r = await self.c.post('/freepublish/submit', json={
            'media_id': media_id
        })
        r = r.json()
        if r.get('errcode') != 0:
            print(r.get('errmsg'))
        return r.get('errcode') == 0


if __name__ == '__main__':
    pass
# asyncio.run(main(), debug=True)
