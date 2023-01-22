import json
import os
from prompt_toolkit import shortcuts, validation

from user import User, InvalidPasswordError

# add custom function for multiline input
from custom_dialogs import multiline_input_dialog
shortcuts.multiline_input_dialog = multiline_input_dialog

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
            
            # create user object
            user = User.new(username, password, data)
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            break

    # prompt for action
    while True:
        action = shortcuts.radiolist_dialog(
            text="Select an action",
            values=[
                ('post_whatsapp', "Send Whatsapp Message"),
                ('post_instagram', "Post to Instagram"),
                ('change_whatsapp_token', "Change Whatsapp Access Token"),
                ('change_instagram_token', "Change Instagram Access Token"),
                ('change_password', "Change Password"),
                ("change_instagram_id", "Change Instagram ID")],
            cancel_text="Exit").run()
        if action == None:
            break
        if action == 'post_whatsapp':
            # prompt for message
            message = shortcuts.multiline_input_dialog(text="Please enter your message").run()
            if message == None: continue
            
            # send message
            whatsapp_response = user.send_whatsapp_message(message, 106161455706789, 4917642602495)
            if whatsapp_response.status_code != 200:    # Error codes: https://developers.facebook.com/docs/whatsapp/on-premises/errors
                error_message = json.loads(whatsapp_response.text)["error"]["message"]
                shortcuts.message_dialog(text= f"An Error occurred: {error_message}").run()
                continue
            shortcuts.message_dialog(text= "Message sent successfully!").run()
        
        elif action == 'post_instagram':
            # prompt for image and caption
            filepath = shortcuts.input_dialog(text="Please enter your image path").run()
            if filepath == None: continue
            if not os.path.isfile(filepath):
                shortcuts.message_dialog(text="File doesn't exist!").run()
                continue
            if not filepath.lower().endswith(('.png','.jpg', '.jpeg')): 
                shortcuts.message_dialog(text="Please use a png or jpg file").run()
                continue
            comment = shortcuts.multiline_input_dialog(text="Add a caption").run()
            if comment == None: continue

            # upload image
            instagram_response = user.post_to_instagram(filepath, comment)
            if instagram_response.status_code != 200:
                error_message = json.loads(instagram_response.text)["error"]["message"]
                shortcuts.message_dialog(text= f"An Error occurred: {error_message}").run()
                continue
            shortcuts.message_dialog(instagram_response.text).run()

        elif action == 'change_whatsapp_token':
            # update the whatsapp access token
            token = shortcuts.input_dialog(text='Please type your new token:').run()
            if token == None: continue
            user.change_token(token, "whatsapp")
            data[user.username] = user.get_user_data()
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        elif action == 'change_instagram_token':
            # update the instagram access token
            token = shortcuts.input_dialog(text='Please type your new token:').run()
            if token == None: continue
            user.change_token(token, "instagram")
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

        elif action == 'change_instagram_id':
            instagram_business_id = shortcuts.input_dialog(text='Please type your new Instagram ID:').run()
            if instagram_business_id == None: continue
            user.change_instagram_id(instagram_business_id)
            with open('secrets.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

                
# def clear_cli():
#     """clears the command line interface"""
#     if os.name == "posix":
#         os.system('clear')
#     else:
#          os.system('cls')


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


if __name__ == "__main__":
    main()
