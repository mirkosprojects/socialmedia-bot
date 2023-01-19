import requests
import json
import hashlib
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from prompt_toolkit import prompt, shortcuts, validation

def main():
    with open('secrets.json', 'r') as f:
        data = json.load(f)

    while True:
        # prompt for login, new user or exit
        result = shortcuts.button_dialog(text='Please choose an action',
                                            buttons=[
                                                ('Login', True),
                                                ('New User', False),
                                                ('Exit', None)]).run()
        if result == None: return
        if result:
            # prompt for username
            username = shortcuts.input_dialog(
                    text='Please type your username:',
                    cancel_text="Exit").run()
            if username == None: continue

            # prompt for password
            password = shortcuts.input_dialog(
                    text='Please type your password:',
                    cancel_text="Exit",
                    password=True).run()
            if password == None: continue

            # create user object
            try:
                user = User(username, password, data)
                break
            except InvalidPasswordError:
                shortcuts.message_dialog(text= "Username and password don't match").run()

        else:
            # prompt for username
            username = shortcuts.input_dialog(
                text='Please type your username:',
                cancel_text="Exit").run()
            if username == None: continue
            if username in data:
                shortcuts.message_dialog(text= "Username not available").run()
                continue

            # prompt for password
            password = shortcuts.input_dialog(
                text='Enter your new password:',
                validator=PasswordValidator(),
                password=True).run()
            if password == None: continue
            password_copy = shortcuts.input_dialog(
                text='Enter your new password again:',
                password=True).run()
            if password_copy == None: continue
            if password != password_copy:
                shortcuts.message_dialog(text= "Passwords don't match").run()
                continue

            # prompt for access token
            token = shortcuts.input_dialog(
                    text='Please type your Access Token:',
                    cancel_text="Exit").run()
            if token == None: continue

            user = User.new(username, password, data, token)
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

 
    # prompt for action
    while True:
        action = shortcuts.radiolist_dialog(
            text="Select an action",
            values=[
                ('send_message', "Send Message"),
                ('update_token', "Update Access Token"),
                ('change_password', "Change Password")
            ],
            cancel_text="Exit"
        ).run()
        if action == None:
            break
        if action == 'send_message':
            # send a whatsapp message
            clear_cli()
            try:
                message = prompt("Please enter your message: [ESC] and [Enter] to finish\n", multiline=True)
            except KeyboardInterrupt:
                pass
            else:
                whatsapp_response = user.send_whatsapp_message(message, 4917642602495)
                if whatsapp_response.status_code == 401:
                    error_message = json.loads(whatsapp_response.text)["error"]["message"]
                    shortcuts.message_dialog(text= f"An Error occurred: {error_message}").run()
                else:
                    shortcuts.message_dialog(text= "Message sent successfully!").run()
            
        elif action == 'update_token':
            # update the whatsapp access token
            token = shortcuts.input_dialog(text='Please type your new token:').run()
            if token == None: continue
            user.change_token(token)
            data[user.username] = user.get_user_data()
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        elif action == 'change_password':
            # change the user password
            old_password = shortcuts.input_dialog(
                text='Enter your old password:',
                password=True).run()
            if old_password == None:
                continue
            if not user.check_password(data, old_password):
                shortcuts.message_dialog(text= "Wrong password!").run()
                continue
            # prompt for new password
            new_password = shortcuts.input_dialog(
                text='Enter your new password:',
                validator=PasswordValidator(),
                password=True).run()
            if new_password == None:
                continue
            new_password_copy = shortcuts.input_dialog(
                text='Enter your new password again:',
                password=True).run()
            if new_password_copy == None:
                continue
            if new_password != new_password_copy:
                shortcuts.message_dialog(text="Passwords don't match").run()
                continue
            if new_password == user.password:
                shortcuts.message_dialog(text="Can't use the same password").run()
                continue

            user.change_password(new_password)
            data[user.username] = user.get_user_data()
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
def clear_cli():
    """clears the command line interface"""
    if os.name == "posix":
        os.system('clear')
    else:
         os.system('cls')


class PasswordValidator(validation.Validator):
    """checks for 12 digit password that contains digits and special characters"""
    def validate(self, document):
        text = document.text
        special_characters = "!@#$%^&*()-+?_=,.<>/"
        if not len(text) > 12:
            raise validation.ValidationError(message='Please use at least 12 characters')
        if not any(c in special_characters for c in text):
            raise validation.ValidationError(message='Please use special characters')
        if not any(c.isdigit() for c in text):
            raise validation.ValidationError(message='Please use numbers')


class InvalidPasswordError(Exception):
    """Exception raised when password doesn't match hash"""
    def __init__(self, message = "Invalid password"):
        self.message = message
        super().__init__(self.message)


class User():
    """User Class containing secret information"""
    def __init__(self, username: str, password: str, data: json):
        self.username = username
        self.password = password
        self.__user_data = None
        if not self.check_password(data):
            raise InvalidPasswordError
        self.decrypt_user_data(data)

    @classmethod
    def new(cls, username: str, password: str, data: json, token: str):
        """creates a new user"""

        # add padding, because of encryption issue
        token, token_length = cls.add_padding(token)

        # create user data
        salt, hash = cls.generate_password_hash(password)

        # encrypt the whatsapp token and save to secrets.json
        encrypted_token = cls.encrypt_token(salt, password, token)
        data.update({
            username:{
                "salt": salt,
                "hash": hash,
                "whatsapp":{
                    "token": encrypted_token,
                    "decrypted token": token,
                    "token length": token_length
                }
            }
        })
        return cls(username, password, data)

    def decrypt_user_data(self, data: json):
        """decrypts user data"""
        self.__user_data = data[self.username]
        salt = self.__user_data["salt"]
        encrypted_token = self.__user_data["whatsapp"]["token"]
        token_length = self.__user_data["whatsapp"]["token length"]
        self.__user_data["whatsapp"]["decrypted token"] = User.decrypt_token(salt, self.password, encrypted_token, token_length)

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
        """sends a whatsapp message"""
        # TODO: response returns access token!
        token = self.__user_data["whatsapp"]["decrypted token"]
        url = "https://graph.facebook.com/v15.0/106161455706789/messages"
        my_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {"messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": receiver_number,
                "type": "text",
                "text": {"body": message}
                }
        return requests.post(url, json = body, headers = my_headers) 

    def change_password(self, new_password):
        # add padding, because of encryption issue
        padded_token, token_length = User.add_padding(self.__user_data["whatsapp"]["decrypted token"])

        salt, hash = User.generate_password_hash(new_password)

        # encrypt the whatsapp token and write to userdata
        encrypted_whatsapptoken = User.encrypt_token(salt, new_password, padded_token)
        self.__user_data["whatsapp"]["token"] = encrypted_whatsapptoken
        self.__user_data["whatsapp"]["decrypted token"] = padded_token
        self.__user_data["whatsapp"]["token length"] = token_length
        self.__user_data["salt"] = salt
        self.__user_data["hash"] = hash
        self.password = new_password

    def change_token(self, token):       
        # add padding, because of encryption issue
        token, token_length = User.add_padding(token)

        # generate new salt and password hash
        salt, hash = User.generate_password_hash(self.password)
        self.__user_data["salt"] = salt
        self.__user_data["hash"] = hash
        
        # encrypt the whatsapp token and save to secrets.json
        encrypted_token = User.encrypt_token(salt, self.password, token)
        self.__user_data["whatsapp"]["token"] = encrypted_token
        self.__user_data["whatsapp"]["decrypted token"] = token
        self.__user_data["whatsapp"]["token length"] = token_length

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


if __name__ == "__main__":
    main()
