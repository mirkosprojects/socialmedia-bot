import asyncio
import pyimgbox
from PIL import Image
import requests
import json
import os
from pathlib import Path

async def upload_images(filepaths):
    async with pyimgbox.Gallery(title="Image for HKA Socialbot") as gallery:
        image_urls = []
        async for submission in gallery.add(filepaths):
            if not submission['success']:
                image_urls.append(submission['error'])
            else:
                image_urls.append(submission['image_url'])
        return image_urls

def export_to_jpg(filepath: str):
    img = Image.open(filepath)
    if img.format != 'JPEG':
        new_img = img.convert('RGB')
        filepath = os.path.join(os.path.dirname(filepath), Path(filepath).stem + '.jpg')
        new_img.save(filepath)
    return filepath

def compare_jsons(template, data, errors = []):
    """compares if keys from template are in data, returns non existing keys"""
    if type(template) == dict:
        for key, item in template.items():
            if key in data:
                compare_jsons(item, data[key], errors)
            else:
                errors.append(key)
    return(errors)

def send_whatsapp_message(message: str, access_token: str, sender_number: int, receiver_number: int):
    """
    sends a whatsapp message
    TODO: response returns access token!
    """
    url = f"https://graph.facebook.com/v15.0/{sender_number}/messages"
    my_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {"messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": receiver_number,
            "type": "text",
            "text": {"body": message}
            }
    return requests.post(url, json = body, headers = my_headers)

def send_whatsapp_image(image_url: str, access_token: str, sender_number: int, receiver_number: int):
    """
    sends an image to whatsapp
    TODO: response returns access token!
    """
    url = f"https://graph.facebook.com/v15.0/{sender_number}/messages"
    my_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {"messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": receiver_number,
            "type": "image",
            "image": {"link": image_url},
            }
    return requests.post(url, json = body, headers = my_headers)


def upload_image_to_host(filepath: str) -> str:
    """uploads an image to a hosting website, returns the url"""
    # export image to jpeg
    filepath = export_to_jpg(filepath)

    # upload images to imgbox.com
    image_urls = asyncio.run(upload_images([filepath]))

    return image_urls[0]

def post_to_instagram(business_id: str, token: str, image_url: str, caption: str):
    """posts an image to instagram"""
    # post image to container
    post_url = f"https://graph.facebook.com/v15.0/{business_id}/media"
    post_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': token
    }
    response = requests.post(post_url, data=post_payload)
    if not 'id' in json.loads(response.text):
        return response
    creation_id = json.loads(response.text)['id']

    # publish image to feed
    publish_url = f"https://graph.facebook.com/v15.0/{business_id}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': token
    }
    return requests.post(publish_url, data=publish_payload)


# relative path tests
# filename = "/Users/mirkoschuerlein/Documents/socialmedia-bot/website/static/uploads/1/test_image2.jpg"
# base_path = "/Users/mirkoschuerlein/Documents/socialmedia-bot/website/templates"
# print(os.path.relpath(filename, base_path))




# Sending image and caption to wa test
# image_url = "https://images2.imgbox.com/63/64/DrZHx7B2_o.jpg"
# access_token = "EAARSQVdd5ZA4BAKtTTovYpYc5QvleUISCiZC8OiX4CF55oGCZBDGWie0hSe1Xv7tdnUqmxjHNgJaZCZCidNS1TKHNB23ZBGGVNaS8e51xHZBfHZBZAz8cjmpRgqw7Sc7dvytl0WZA3WEyK2VZBQpBXpEWPREz0jvm94gCM2PlPHhhL5gTcUEiCYAlzp"
# sender = 106161455706789
# receiver = 4917642602495
# whatsapp_response = send_whatsapp_image(image_url, access_token, sender, receiver)
# # send_whatsapp_message("test", access_token, sender, receiver)
# print(json.loads(whatsapp_response.text))
# content_id = whatsapp_response.json
# print(content_id["messages"])


# whatsapp_response = send_whatsapp_message("test", access_token, sender, receiver, "wamid.HBgNNDkxNzY0MjYwMjQ5NRUCABEYEjYyOENEQzM3MDI3Qjk1MUMyNQA=")
# print(json.loads(whatsapp_response.text))
