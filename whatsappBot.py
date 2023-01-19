import requests
import json
import hashlib
import base64
import os
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from prompt_toolkit import prompt, shortcuts, validation

def main():
    with open('secrets.json', 'r') as f:
        data = json.load(f)

    while True:
        # ask for login or new user
        result = shortcuts.radiolist_dialog(text='Please choose an action',
                                            values=[
                                                (1, "Login"),
                                                (2, "New User")]).run()
        if result == None: 
            return
        if result == 1:
            data, user_data, username, password, salt = login_user(data)
            if not None in [data, user_data, username, password, salt]:
                break
        if result == 2:
            data, user_data, username, password, salt = create_user(data)
            if not None in [data, user_data, username, password, salt]:
                print(data)
                with open('secrets.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                break

        
    # Ask for preferred action
    while True:
        action = shortcuts.radiolist_dialog(
            text="Select an action",
            values=[
                (1, "Update Token"),
                (2, "Send Message"),
                (3, "Change Password")
            ],
            cancel_text="Exit"
        ).run()
        if action == None:
            break
        if action == 1:
            whatsapptoken = shortcuts.input_dialog(
                text='Please type your new token:').run()
            if whatsapptoken != None:
                # add padding, because of encryption issue
                token_length = len(whatsapptoken)
                padding = "X" * (4 - (len(whatsapptoken) % 4))
                if padding == "XXXX": padding = ""
                whatsapptoken += padding

                # generate new salt and password hash
                salt, hash = generate_password_hash(password)
                user_data["salt"] = salt
                user_data["hash"] = hash
                
                # encrypt the whatsapp token and save to secrets.json
                encrypted_whatsapptoken = encrypt_token(salt, password, whatsapptoken)
                user_data["whatsapp"]["token"] = encrypted_whatsapptoken
                user_data["whatsapp"]["original token"] = whatsapptoken
                user_data["whatsapp"]["token length"] = token_length
                
                # update user data and save to secrets.json
                data[username] = user_data
                with open('secrets.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

        elif action == 2:
            # ask for message
            clear_cli()
            try:
                message = prompt("Please enter your message: [ESC] and [Enter] to finish\n", multiline=True)
            except KeyboardInterrupt:
                pass
            else:
                # get decrypted whatsapp access token
                decrypted_whatsapptoken = decrypt_token(salt,
                                                        password,
                                                        user_data["whatsapp"]["token"],
                                                        user_data["whatsapp"]["token length"])

                # send a message to whatsapp
                whatsapp_response = post_WA_message(decrypted_whatsapptoken, message, 4917642602495)

        elif action == 3:
            data, user_data, password, salt = update_password(data, user_data, username, password, salt)
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            
def clear_cli():
    """clears the command line interface"""
    if os.name == "posix":
        os.system('clear')
    else:
         os.system('cls')

def post_WA_message(token: str, message: str, receiver_number: int) -> str:
    url = "https://graph.facebook.com/v15.0/106161455706789/messages"
    my_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": receiver_number,
            "type": "text",
            "text": {"body": message}
            }
    wa_response = requests.post(url, json = body, headers = my_headers)
    return wa_response.text

def check_password(secrets: json, username: str, password: str) -> json:
    """verify username and password combination, return user information"""
    if username in secrets:
        salt = base64.b64decode(secrets[username]["salt"])
        hash = base64.b64decode(secrets[username]["hash"])
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        if key == hash:
            return secrets[username]
    return None

def generate_password_hash(password: str):
    """generates salt and password hash"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt = base64.b64encode(salt).decode('ascii')
    key = base64.b64encode(key).decode('ascii')
    return salt, key

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

def login_user(data: json):
     # Ask for username and password
    username = shortcuts.input_dialog(
            text='Please type your username:',
            cancel_text="Exit").run()
    if username == None: return data, None, None, None, None
    password = shortcuts.input_dialog(
            text='Please type your password:',
            cancel_text="Exit",
            password=True).run()
    if password == None: return data, None, username, None, None

    # user login
    user_data = check_password(data, username, password)
    if user_data == None:
        shortcuts.message_dialog(text="Username and Password don't match").run()
        return data, None, username, password, None
    else:
        salt = user_data["salt"]
        return data, user_data, username, password, salt 

def create_user(data: json):
    """creates a new user"""
    # password validator
    password_validator = validation.Validator.from_callable(
        password_validation_func,
        error_message=  "Password has to be at least 12 digits long "
                        "and contain special characters and numbers",
        move_cursor_to_end=True)

    # ask for username
    while True:
        username = shortcuts.input_dialog(
            text='Please type your username:',
            cancel_text="Exit").run()
        if username == None: return data, None, None, None, None
        if username in data:
            shortcuts.message_dialog(text= "Username not available").run()
            return data, None, None, None, None
        else:
            break
    # prompt for username, password and Access Token
    password = shortcuts.input_dialog(
        text='Enter your new password:',
        validator=password_validator,
        password=True).run()
    if password == None:
        return data, None, username, None, None
    password_copy = shortcuts.input_dialog(
        text='Enter your new password again:',
        password=True).run()
    if password_copy == None:
        return data, None, username, None, None
    if password != password_copy:
        shortcuts.message_dialog(text= "Passwords don't match").run()
        return data, None, username, None, None
    whatsapptoken = shortcuts.input_dialog(
            text='Please type your Access Token:',
            cancel_text="Exit").run()
    if whatsapptoken == None:
        return data, None, username, password, None

    # add padding, because of encryption issue
    token_length = len(whatsapptoken)
    padding = "X" * (4 - (len(whatsapptoken) % 4))
    if padding == "XXXX": padding = ""
    whatsapptoken += padding

    # create user data
    salt, hash = generate_password_hash(password)

    # encrypt the whatsapp token and save to secrets.json
    encrypted_whatsapptoken = encrypt_token(salt, password, whatsapptoken)
    data.update({
        username:{
            "salt": salt,
            "hash": hash,
            "whatsapp":{
                "token": encrypted_whatsapptoken,
                "original token": whatsapptoken,
                "token length": token_length
            }
        }
    })
    user_data = data[username]
    return data, user_data, username, password, salt


def update_password(data: json, user_data: json, username: str, password: str, salt: str):
    original_data = data
    original_user_data = user_data
    original_password = password
    original_salt = salt

    password_validator = validation.Validator.from_callable(
        password_validation_func,
        error_message=  "Password has to be at least 12 digits long "
                        "and contain special characters and numbers",
        move_cursor_to_end=True)

    old_password = shortcuts.input_dialog(
        text='Enter your old password:',
        password=True).run()
    if old_password == None:
        return original_data, original_user_data, original_password, original_salt
    if check_password(data, username, old_password) == None:
        shortcuts.message_dialog(text= "Wrong password!").run()
        return original_data, original_user_data, original_password, original_salt
    # ask for new password
    new_password = shortcuts.input_dialog(
        text='Enter your new password:',
        validator=password_validator,
        password=True).run()
    if new_password == None:
        return original_data, original_user_data, original_password, original_salt
    new_password_copy = shortcuts.input_dialog(
        text='Enter your new password again:',
        password=True).run()
    if new_password_copy == None:
        return original_data, original_user_data, original_password, original_salt
    if new_password != new_password_copy:
        shortcuts.message_dialog(text="Passwords don't match").run()
        return original_data, original_user_data, original_password, original_salt
    if new_password == original_password:
        shortcuts.message_dialog(text="Can't use the same password").run()
        return original_data, original_user_data, original_password, original_salt
    # load and decrypt hash
    decrypted_whatsapptoken = decrypt_token(salt,
                password,
                user_data["whatsapp"]["token"],
                user_data["whatsapp"]["token length"])

    # add padding, because of encryption issue
    token_length = len(decrypted_whatsapptoken)
    padding = "X" * (4 - (len(decrypted_whatsapptoken) % 4))
    if padding == "XXXX": padding = ""
    decrypted_whatsapptoken += padding

    salt, hash = generate_password_hash(new_password)

    # encrypt the whatsapp token and save to secrets.json
    encrypted_whatsapptoken = encrypt_token(salt, new_password, decrypted_whatsapptoken)
    user_data["whatsapp"]["token"] = encrypted_whatsapptoken
    user_data["whatsapp"]["original token"] = decrypted_whatsapptoken
    user_data["whatsapp"]["token length"] = token_length
    user_data["salt"] = salt
    user_data["hash"] = hash
    password = new_password
    data[username] = user_data

    return data, user_data, password, salt


if __name__ == "__main__":
    main()
