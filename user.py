import asyncio
import base64
import hashlib
import json
import os
import requests
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from media_upload import export_to_jpg, upload_images
from helpers import compare_jsons


class InvalidPasswordError(Exception):
    """Exception raised when password doesn't match hash"""
    def __init__(self, message = "Wrong Password!"):
        self.message = message
        super().__init__(self.message)


class InvalidUserDataError(Exception):
    """Exception raised when there are missing keys in the user data"""
    def __init__(self, errors):
        self.message = f"There are missing keys for this user: {', '.join(errors)}"
        super().__init__(self.message)


class User():
    """User Class containing secret information"""
    def __init__(self, username: str, password: str, data: json, template: json):
        self.username = username
        self.password = password
        self.__user_data = None
        self.available_messengers = [messenger for messenger in template if messenger not in ["salt", "hash"]]

        if not self.check_password(data):
            raise InvalidPasswordError
        self.decrypt_user_data(data)

        user_data_errors = compare_jsons(template, self.__user_data)
        if user_data_errors:
            raise InvalidUserDataError(user_data_errors)

    @classmethod
    def new(cls, username: str, password: str, data: json, template: json):
        """creates a new user"""

        # create user data
        salt, hash = cls.generate_password_hash(password)
        data.update({username: template})
        data[username]["salt"] = salt
        data[username]["hash"] = hash
        
        return cls(username, password, data, template)

    def decrypt_user_data(self, data: json):
        """decrypts user data"""
        self.__user_data = data[self.username]
        salt = self.__user_data["salt"]
        for messenger in self.available_messengers:
            encrypted_token = self.__user_data[messenger]["token"]
            token_length = self.__user_data[messenger]["token length"]
            try:
                self.__user_data[messenger]["decrypted token"] = User.decrypt_token(salt, self.password, encrypted_token, token_length)
            except Exception as e:
                print(e)
    
    def check_password(self, data, password = None) -> bool:
        """checks password against hash"""
        if password == None: password = self.password
        if not self.username in data:
            return False
        salt = base64.b64decode(data[self.username]["salt"])
        hash = base64.b64decode(data[self.username]["hash"])
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return key == hash

    def generate_password_hash(password: str):
        """generates salt and password hash"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        salt = base64.b64encode(salt).decode('ascii')
        key = base64.b64encode(key).decode('ascii')
        return salt, key

    def add_padding(token: str):
        """adds padding to the input token, so it's divisible by 4"""
        length = len(token)
        padding = "X" * (4 - (len(token) % 4))
        if padding == "XXXX": padding = ""
        token += padding
        return token, length

    def get_user_data(self):
        """retreives enrypted user data"""
        data = self.__user_data
        # data["decrypted token"] = ""
        return data

    def send_whatsapp_message(self, message: str, receiver_number: int):
        """
        sends a whatsapp message
        TODO: response returns access token!
        """
        sender_number = self.__user_data["whatsapp"]["phone number"]
        token = self.__user_data["whatsapp"]["decrypted token"]
        url = f"https://graph.facebook.com/v15.0/{sender_number}/messages"
        my_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {"messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": receiver_number,
                "type": "text",
                "text": {"body": message}
                }
        return requests.post(url, json = body, headers = my_headers) 

    def post_to_instagram(self, filepath: str, caption: str):
        """posts an image to instagram"""
        # export image to jpeg
        filepath = export_to_jpg(filepath)

        # upload images to imgbox.com
        image_urls = asyncio.run(upload_images([filepath]))

        # instagram parameters
        business_id = self.__user_data["instagram"]["business id"]
        
        # post image to container
        post_url = f"https://graph.facebook.com/v15.0/{business_id}/media"
        post_payload = {
            'image_url': image_urls[0],
            'caption': caption,
            'access_token': self.__user_data["instagram"]["decrypted token"]
        }
        response = requests.post(post_url, data=post_payload)
        if not 'id' in json.loads(response.text):
            return response
        creation_id = json.loads(response.text)['id']

        # publish image to feed
        publish_url = f"https://graph.facebook.com/v15.0/{business_id}/media_publish"
        publish_payload = {
            'creation_id': creation_id,
            'access_token': self.__user_data["instagram"]["decrypted token"]
        }
        return requests.post(publish_url, data=publish_payload)
        
    def change_password(self, new_password):
        salt, hash = User.generate_password_hash(new_password)

        # encrypt the access tokens and write to userdata
        for messenger in self.available_messengers:
            # add padding, because of encryption issue
            padded_token, token_length = User.add_padding(self.__user_data[messenger]["decrypted token"])
            encrypted_token = User.encrypt_token(salt, new_password, padded_token)
            self.__user_data[messenger]["token"] = encrypted_token
            self.__user_data[messenger]["decrypted token"] = padded_token
            self.__user_data[messenger]["token length"] = token_length
        self.__user_data["salt"] = salt
        self.__user_data["hash"] = hash
        self.password = new_password

    def change_token(self, token: str, messenger: str):
        """changes the access token of a messenger"""
        # add padding, because of encryption issue
        token, token_length = User.add_padding(token)
        
        # encrypt the access token write to userdata
        encrypted_token = User.encrypt_token(self.__user_data["salt"], self.password, token)
        self.__user_data[messenger]["token"] = encrypted_token
        self.__user_data[messenger]["decrypted token"] = token[0:token_length]
        self.__user_data[messenger]["token length"] = token_length

    def change_instagram_id(self, id: int):
        """changes the instagram business id"""
        if "business id" in self.__user_data["instagram"]:
            self.__user_data["instagram"]["business id"] = id
        else:
            self.__user_data["instagram"].update({
                "business id": id
            })

    def change_whatsapp_number(self, number: int):
        """changes the instagram business id"""
        if "phone number" in self.__user_data["whatsapp"]:
            self.__user_data["whatsapp"]["phone number"] = number
        else:
            self.__user_data["whatsapp"].update({
                "phone number": number
            })

    def decrypt_token(salt: str, password: str, token: str, length: int) -> str:
        """decrypts the access token"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=base64.b64decode(salt),
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        f = Fernet(key)
        decrypted_token = f.decrypt(base64.b64decode(token))
        return base64.b64encode(decrypted_token).decode('ascii')[0:length]

    def encrypt_token(salt: str, password: str, token: str) -> bytes:
        """encrypts the access token"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=base64.b64decode(salt),
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        f = Fernet(key)
        encrypted_token = f.encrypt(base64.b64decode(token))
        return base64.b64encode(encrypted_token).decode('ascii')