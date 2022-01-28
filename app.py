import asyncio
from typing import Optional

from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, UploadFile, Form, HTTPException
from starlette.responses import JSONResponse

from config import TOKEN
from mp import Mp
from utils import markdown_to_html

app = FastAPI()


async def upload_article(markdown: str, publish=True) -> bool:
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
            author=metadata.get('author')
        )
        return await mp.publish(media_id) if publish else bool(media_id)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    if not request.headers.get('Authorization', '') == TOKEN:
        return JSONResponse(status_code=401)
    else:
        response = await call_next(request)
        return response


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post('/articles', status_code=201)
async def post_article(file: UploadFile, publish: Optional[bool] = Form(default=True)):
    markdown = await file.read()
    markdown = markdown.decode('utf-8')
    result = await upload_article(markdown=markdown, publish=publish)
    if not result:
        raise HTTPException(500)
    return {'message': 'success'}


if __name__ == '__main__':
    with open('data/md.md', encoding='utf-8') as f:
        markdown = f.read()
    asyncio.run(upload_article(markdown=markdown, publish=False), debug=True)
