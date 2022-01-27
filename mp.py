import asyncio
import time
from typing import Union

import httpx

from app import APP_ID, APP_SECRET, db

BASE_URL = 'https://api.weixin.qq.com/cgi-bin'


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

    async def _create_client(self):
        return httpx.AsyncClient(
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

    async def upload_material(self, file: bytes, mime_type='image'):
        r = await self.c.post(
            '/material/add_material',
            params={'type': mime_type},
            files={'media': file}
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
        # TODO: 超过 10M 图片压缩，仅支持 bmp/png/jpeg/jpg/gif
        return await self.upload_material(image)


async def main():
    async with Mp() as mp:
        print(await mp.upload_image('data/image.jpg'))


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
