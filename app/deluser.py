import os
from . import db
from app import create_app
from models import User

def del_user(user_id):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        user = User.query.filter_by(id=user_id).first()
        print "user found !!!!!!!!" 
        db.session.delete(user)
        db.session.commit()
        print "user deleted !!!!!!!!" 
