import io

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def preprocess_image(image: bytes, size=10) -> bytes:
    """
    Reformat image to jpeg and resize it if necessary.
    Args:
        image:
        size:
    Returns:

    """
    image = Image.open(io.BytesIO(image))
    print(image.format)
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
    return bytes_io.getvalue()


if __name__ == '__main__':
    with open('data/webp.webp', 'rb') as f:
        preprocess_image(f.read())
