#!/usr/bin/env python3

import json
import os
from prompt_toolkit import shortcuts, validation

from user import User, InvalidPasswordError, InvalidUserDataError

# add custom function for multiline input
from custom_dialogs import multiline_input_dialog
shortcuts.multiline_input_dialog = multiline_input_dialog

secrets = os.path.join(os.path.dirname(__file__), '.secrets.json')
template = os.path.join(os.path.dirname(__file__), 'template.json')
contacts = os.path.join(os.path.dirname(__file__), 'contacts')

def main():
    with open(secrets, 'r') as f:
        data = json.load(f)
    
    with open(template, 'r') as f:
        data_template = json.load(f)

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
                user = User(username, password, data, data_template)
                break
            except InvalidPasswordError:
                shortcuts.message_dialog(text= "Username and password don't match").run()
            except InvalidUserDataError as e:
                shortcuts.message_dialog(text= e.message).run()
                break

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
            user = User.new(username, password, data, data_template)
            with open(secrets, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            break

    # prompt for action
    while True:
        action = shortcuts.radiolist_dialog(
            text="Select an action",
            values=[
                ('post_whatsapp', "Send Whatsapp Message"),
                ('post_instagram', "Post to Instagram"),
                ("settings", "Settings")],
            cancel_text="Exit").run()

        if action == None:
            break

        if action == 'post_whatsapp':
            # prompt for message and contact list
            message = shortcuts.multiline_input_dialog(text="Please enter your message").run()
            if message == None: continue

            contact_lists = [os.path.splitext(f)[0] for f in os.listdir(contacts) if f.endswith(".json")]
            buttons = [(contact_list, contact_list) for contact_list in contact_lists]
            receiver_numbers = shortcuts.radiolist_dialog(
                        text="Select a contact list",
                        values=buttons).run()
            if receiver_numbers == None: continue

            with open(os.path.join(contacts, receiver_numbers) + ".json", 'r') as f:
                contact_list = json.load(f)
            
            # send messages
            error_messages = []
            for number in contact_list:
                whatsapp_response = user.send_whatsapp_message(message, number)
                if whatsapp_response.status_code != 200:    # Error codes: https://developers.facebook.com/docs/whatsapp/on-premises/errors
                    error_messages.append(json.loads(whatsapp_response.text)["error"]["message"])
            
            delivered_messages = len(contact_list) - len(error_messages)
            total_messages = len(contact_list)

            # show error or success
            if not error_messages:
                shortcuts.message_dialog(text= f"{delivered_messages}/{total_messages} messages were delivierd succesfully!").run()
            else:
                formatted_error_messages = '\n'.join(error_messages)
                shortcuts.message_dialog(text= f"{delivered_messages}/{total_messages} messages were delivierd succesfully!\nSome errors occured: \n{formatted_error_messages}").run()
        
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

        # elif action == "edit_contacts":
        #     # prompt for contactlist name
        #     contact_list_name = shortcuts.input_dialog(text='Please type the name of your contactlist:').run()
        #     if contact_list_name == None: continue
        #     contact_list_path = os.path.join(contacts, contact_list_name + ".json")
        #     if os.path.exists(contact_list_path):
        #         with open(contact_list_path, 'r') as f:
        #             contact_list = json.load(f)
        #         for idx, phone_number in enumerate(contact_list):
        #             new_number = shortcuts.input_dialog(text=str(phone_number), ok_text='Change').run()
        #             if new_number != None:
        #                 contact_list[idx] = int(new_number)

        #     with open(contact_list_path, 'w', encoding='utf-8') as f:
        #         json.dump(contact_list, f, ensure_ascii=False, indent=4)

            # TODO: New contact list
            # TODO: Delete contact list


        elif action == 'settings':
            while True:
                action = shortcuts.radiolist_dialog(
                    text="Select an action",
                    values=[
                        ('change_whatsapp_token', "Change Whatsapp Access Token"),
                        ('change_instagram_token', "Change Instagram Access Token"),
                        ('change_password', "Change Password"),
                        ("change_instagram_id", "Change Instagram ID"),
                        ("change_whatsapp_number", "Change Whatsapp number")],
                    cancel_text="Back").run()

                if action == None:
                    break

                elif action == 'change_whatsapp_token':
                    # update the whatsapp access token
                    token = shortcuts.input_dialog(text='Please type your new token:').run()
                    if token == None: continue
                    user.change_token(token, "whatsapp")
                    data[user.username] = user.get_user_data()
                    with open(secrets, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                elif action == 'change_instagram_token':
                    # update the instagram access token
                    token = shortcuts.input_dialog(text='Please type your new token:').run()
                    if token == None: continue
                    user.change_token(token, "instagram")
                    data[user.username] = user.get_user_data()
                    with open(secrets, 'w', encoding='utf-8') as f:
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
                    with open(secrets, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                elif action == 'change_instagram_id':
                    instagram_business_id = shortcuts.input_dialog(text='Please type your new Instagram ID:').run()
                    if instagram_business_id == None: continue
                    user.change_instagram_id(instagram_business_id)
                    with open(secrets, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                elif action == 'change_whatsapp_number':
                    whatsapp_phone_number = shortcuts.input_dialog(text='Please type your new phone number:').run()
                    if whatsapp_phone_number == None: continue
                    user.change_whatsapp_number(whatsapp_phone_number)
                    with open(secrets, 'w', encoding='utf-8') as f:
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
