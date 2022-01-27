import io
import os
import time

import pyperclip
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By

from config import PROXY, DOOCS_MD_URL

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


chrome_options = webdriver.ChromeOptions()
if PROXY:
    chrome_options.add_argument(f'--proxy-server={PROXY}')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_experimental_option('prefs', {
    'download.default_directory': os.getcwd()
})
driver = webdriver.Chrome(options=chrome_options)
driver.get(DOOCS_MD_URL)
time.sleep(2)
action = ActionChains(driver)
action.click(
    driver.find_element(by=By.CSS_SELECTOR, value='.el-switch')
).perform()


def markdown_to_html(content: str) -> str:
    e = driver.find_element(by=By.CSS_SELECTOR, value='.CodeMirror textarea')
    action.click(e).perform()
    e.send_keys(Keys.CONTROL, 'a')
    e.send_keys(Keys.BACKSPACE)
    pyperclip.copy(content)
    e.send_keys(Keys.CONTROL, 'v')
    time.sleep(0.5)
    action.click(
        driver.find_element(by=By.CSS_SELECTOR, value='.el-icon-document')
    ).perform()
    time.sleep(1)
    with open('content.html', encoding='utf-8') as f:
        content = f.read()
    os.remove('content.html')
    print(content)
    return content


if __name__ == '__main__':
    with open('data/md.md', 'r', encoding='utf-8') as f:
        html = markdown_to_html(f.read())
    with open('data/html.html', 'w', encoding='utf-8') as f:
        f.write(html)
