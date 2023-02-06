from . import db
from flask_login import UserMixin

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(12))
    email = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    username = db.Column(db.String(150))
    business_id = db.Column(db.String(30))
    access_token = db.Column(db.String(300))
    phone_number = db.Column(db.String(30))
    contacts = db.relationship('Contact')
