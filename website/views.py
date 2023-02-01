from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Contact
import os
import json
# from user import User as userclass, InvalidPasswordError, InvalidUserDataError
from werkzeug.utils import secure_filename
from helpers import send_whatsapp_message, send_whatsapp_image, post_to_instagram, upload_image_to_host
from . import db, UPLOAD_FOLDER, BASE_FOLDER

TEMPLATE_FOLDER = os.path.join(BASE_FOLDER, "templates")
SPACEHOLDER_UPLOAD = os.path.join(BASE_FOLDER, "static", "upload.png")
views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    image = SPACEHOLDER_UPLOAD
    text = ""
    image_url = ""
    # get request for user page
    if request.method == "GET":
        # create relative path for html
        rel_image_path = os.path.relpath(image, TEMPLATE_FOLDER)
        return render_template("user_page.html", user=current_user, user_image=rel_image_path, user_text=text)

    # post request for user page
    elif request.method == 'POST':
        # check if user submitted text or an image
        text = request.form.get('text_input')
        if not text and not request.files['uploaded-file'].filename:
            flash("Nothing to post!", category="error")

        # get the uploaded file and upload it to webhost
        if request.files['uploaded-file'].filename != "":
            uploaded_img = request.files['uploaded-file']
            img_filename = secure_filename(uploaded_img.filename)
            file_path = os.path.join(BASE_FOLDER, "static", "uploads", str(current_user.id), img_filename)
            if not os.path.exists(os.path.dirname(file_path)):
                os.mkdir(os.path.dirname(file_path))
            uploaded_img.save(file_path)
            image = file_path
            image_url = upload_image_to_host(file_path)
        rel_image_path = os.path.relpath(image, TEMPLATE_FOLDER)
        if request.form.get('text_input'):
            text = request.form.get('text_input')

        # post image from session on instagram
        if request.form.get('instagram', False):
            if image_url:
                post_to_instagram(current_user.business_id, current_user.access_token, image_url, text)
                flash("Successfully posted to Instagram!", category='success')
            else:
                flash("Please select an image before posting to Instagram!", category='error')
        
        # post image and or text to whatsapp
        if request.form.get('whatsapp', False):
            error_messages_img = []
            error_messages_msg = []
            for contact in current_user.contacts:
                receiver_number = contact.phone_number
                if image_url:
                    whatsapp_img_response = send_whatsapp_image(image_url, current_user.access_token, current_user.phone_number, receiver_number)
                    if whatsapp_img_response.status_code != 200:    # Error codes: https://developers.facebook.com/docs/whatsapp/on-premises/errors
                        error = json.loads(whatsapp_img_response.text)["error"]["message"]
                        error_messages_img.append(f"Name: {contact.name}, {error}")
                if text:
                    whatsapp_msg_response = send_whatsapp_message(text, current_user.access_token, current_user.phone_number, receiver_number)
                    if whatsapp_msg_response.status_code != 200:    # Error codes: https://developers.facebook.com/docs/whatsapp/on-premises/errors
                        error = json.loads(whatsapp_msg_response.text)["error"]["message"]
                        error_messages_msg.append(f"Name: {contact.name}, {error}")

            delivered_images = len(current_user.contacts) - len(error_messages_img)
            delivered_messages = len(current_user.contacts) - len(error_messages_msg)
            total_messages = len(current_user.contacts)

            # show error or success
            if not error_messages_img and image_url:
                flash(f"{delivered_images}/{total_messages} images were delivierd succesfully!", category="success")
            elif image_url:
                formatted_error_messages = '\n'.join(error_messages_img)
                flash(f"{delivered_images}/{total_messages} images were delivierd succesfully!\nSome errors occured: \n{formatted_error_messages}", category="error")
            if not error_messages_msg and text:
                flash(f"{delivered_messages}/{total_messages} messages were delivierd succesfully!", category="success")
            elif text:
                formatted_error_messages = '\n'.join(error_messages_msg)
                flash(f"{delivered_messages}/{total_messages} messages were delivierd succesfully!\nSome errors occured: \n{formatted_error_messages}", category="error")     

        # post image and or text to facebook
        if request.form.get('facebook', False):
            print("publishing facebook post...")

        # post image and or text to twitter
        if request.form.get('twitter', False):
            print("publishing twitter post...")

        # post image and or text to snapchat
        if request.form.get('snapchat', False):
            print("publishing snapchat post...")
        
        # post image and or text to linkedin
        if request.form.get('linkedin', False):
            print("publishing linkedin post...")
    
        # create relative path for html
        rel_image_path = os.path.relpath(image, TEMPLATE_FOLDER)
        return render_template("user_page.html", user=current_user, user_image=rel_image_path, user_text=text)
    else:
        return render_template("user_page.html", user=current_user)

@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if request.form.get('update_whatsapp_button', False):
            if request.form.get('whatsapp_token'):
                whatsapp_token = str(request.form.get('whatsapp_token'))    
                flash(f"Updated access token! \n {whatsapp_token}", category='success')
                current_user.access_token = whatsapp_token
            if request.form.get('whatsapp_number'):
                whatsapp_number = str(request.form.get('whatsapp_number'))
                flash(f"Updated phone number! \n {whatsapp_number}", category='success')
                current_user.phone_number = whatsapp_number
        if request.form.get('update_instagram_button', False):
            if request.form.get('instagram_token'):
                instagram_token = str(request.form.get('instagram_token'))
                flash(f"Updated access token! \n {instagram_token}", category='success')
                current_user.access_token = instagram_token
            if request.form.get('instagram_id'):
                instagram_id = str(request.form.get('instagram_id'))
                flash(f"Updated business id! \n {instagram_id}", category='success')
                current_user.business_id = instagram_id
        if request.form.get('update_facebook_button', False):
            if request.form.get('facebook_token'):
                facebook_token = str(request.form.get('facebook_token'))
                flash(f"Updated access token! \n {facebook_token}", category='success')
                current_user.access_token = facebook_token
            if request.form.get('facebook_id'):
                facebook_id = str(request.form.get('facebook_id'))
                flash(f"Updated business id! \n {facebook_id}", category='success')
                current_user.business_id = facebook_id
        if request.form.get('contact_name') and request.form.get('contact_email') and request.form.get('contact_number'):
            name = request.form.get('contact_name')
            email = request.form.get('contact_email')
            number = request.form.get('contact_number')
            new_contact = Contact(name=name, phone_number=number, email=email, user_id= current_user.id)
            db.session.add(new_contact)
            flash('Contact added!', category='success')

    data = {
    'whatsapp_token': current_user.access_token,
    'whatsapp_number': current_user.phone_number,
    'instagram_token': current_user.access_token,
    'instagram_id': current_user.business_id,
    'facebook_token': current_user.access_token,
    'facebook_id': current_user.business_id
    }
    db.session.commit()
    return render_template("settings.html", user=current_user, data=data)

@views.route('/delete-contact', methods=['POST'])
def delete_contact():  
    contact = json.loads(request.data)
    contact_id = contact['contact_id']
    contact = Contact.query.get(contact_id)
    if contact:
        if contact.user_id == current_user.id:
            db.session.delete(contact)
            db.session.commit()

    return jsonify({})