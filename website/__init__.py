from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
DB_NAME = "database.db"
UPLOAD_FOLDER = "../static/uploads"
BASE_FOLDER = "/Users/mirkoschuerlein/Documents/socialmedia-bot/website"

def create_app():
    app = Flask(__name__)
    app.secret_key = "ijasdfbk1234nasdß90<123%$&$/"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Contact

    with app.app_context():
        db.create_all()
    print("Database was created")

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app
