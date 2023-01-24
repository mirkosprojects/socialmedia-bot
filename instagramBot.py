import asyncio
import requests
import json
from media_upload import upload_images


def main():
    # upload images to imgbox.com
    image_urls = asyncio.run(upload_images(["image.jpg", "image1.png"]))
    print(image_urls)

    # instagram parameters
    business_id = 17841457312980118
    caption = "Test caption #Hashtag #cool"
    token = "EAARSQVdd5ZA4BAGdwBAcINbsrvDpm9XBGJ1TWKD0csPa4lbbDsqGeB6eBcIZCOVez6HSGL1s8vZCVzwfmyfeJ2hdj98WKrMz1Q79UnlqZBB2aXbCnPOSGghBiElqGetjJwonxCZB9OiFGL8di421bIFgwhGtwkUT8qqIEljyVSgaTZAx8q34ZB9DFkn27vO7OncFEZCXwZA5OI5oZAMelSkZB4t"
    
    # post image to container
    post_url = f"https://graph.facebook.com/v15.0/{business_id}/media"
    post_payload = {
        'image_url': image_urls[0],
        'caption': caption,
        'access_token': token
    }
    r = requests.post(post_url, data=post_payload)
    result = json.loads(r.text)
    if not 'id' in result:
        print(result["error"]["message"])
        return
    creation_id = result['id']

    # publish image to feed
    publish_url = f"https://graph.facebook.com/v15.0/{business_id}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': token
    }
    r = requests.post(publish_url, data=publish_payload)
    print(r.text)

if __name__ == '__main__':
    main()