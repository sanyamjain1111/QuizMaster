import os
from flask import Flask
from application import config
from application.config import LocalDevelopementConfig
from application.database import db
from flask_mail import Mail

app=None
mail=Mail()
def create_app():
    app=Flask(__name__, template_folder="templates", static_folder='static')    
    app.secret_key = "jain1111"
    if os.getenv('ENV',"developement")=="production":
        raise Exception("Currently no production config is setup.")
    else:
        print("Starting Local Developement")
        app.config.from_object(LocalDevelopementConfig)
    db.init_app(app)
    app.app_context().push()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db?timeout=30'
    app.config['SQLALCHEMY_ECHO'] = True
    os.makedirs('static/upload', exist_ok=True)
    app.config["UPLOAD_FOLDER"] = "static/upload"
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') 
    app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

    mail.init_app(app) 
    return app

app=create_app()
with app.app_context():
    db.create_all()
from application.controllers import *
if __name__== '__main__':
    app.run(host='0.0.0.0',
            debug=True,
            port=5001)  