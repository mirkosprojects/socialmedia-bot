import asyncio

import pyimgbox
from PIL import Image

# # Uncomment this to enable debugging messages
# import logging
# logging.basicConfig(level=logging.DEBUG)


# Using Gallery as an asynchronous context manager is the simplest usage.
# https://github.com/plotski/pyimgbox/blob/master/examples.py
async def upload_images(filepaths):
    async with pyimgbox.Gallery(title="Image for HKA Socialbot") as gallery:
        image_urls = []
        async for submission in gallery.add(filepaths):
            if not submission['success']:
                image_urls.append(submission['error'])
            else:
                image_urls.append(submission['image_url'])
        return image_urls

def export_to_jpg(original_path: str , new_path: str = 'img.jpg'):
    img = Image.open(original_path)
    new_img = img.convert('RGB')
    new_img.save(new_path)
    return new_path
    

if __name__ == '__main__':
    jpg_image = export_to_jpg("image2.jpg")
    image_urls = asyncio.run(upload_images([jpg_image]))
    print(image_urls)